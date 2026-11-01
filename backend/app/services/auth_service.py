from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.tables import VersaoSchema
from app.models import Usuario

SESSION_COOKIE = "nexo_user_session"
SESSION_ISSUER = "nexo-estoque"
SESSION_LIFETIME = timedelta(hours=12)
SESSION_LIFETIME_SECONDS = int(SESSION_LIFETIME.total_seconds())
AUTH_CONFIGURATION_ERROR = "Autenticação indisponível. Configure segredos fortes no servidor."
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_KEY_LENGTH = 32
USERNAME_SCHEMA_VERSION = 4
USERNAME_SCHEMA_ERROR = "A migração de username obrigatório ainda não foi concluída."


def username_schema_ready(db: Session) -> bool:
    return db.scalar(
        select(VersaoSchema.versao).where(VersaoSchema.versao == USERNAME_SCHEMA_VERSION)
    ) is not None


def require_username_schema(db: Session, *, lock: bool = False) -> None:
    statement = select(VersaoSchema.versao).where(VersaoSchema.versao == USERNAME_SCHEMA_VERSION)
    if lock:
        statement = statement.with_for_update()
    if db.scalar(statement) is None:
        raise HTTPException(status_code=503, detail=USERNAME_SCHEMA_ERROR)


def _session_secret() -> str:
    secret = os.getenv("NEXO_SESSION_SECRET", "")
    if not 32 <= len(secret.encode("utf-8")) <= 256:
        raise HTTPException(status_code=503, detail=AUTH_CONFIGURATION_ERROR)
    return secret


def _bootstrap_key() -> str:
    key = os.getenv("NEXO_ADMIN_BOOTSTRAP_KEY", "")
    if not 32 <= len(key.encode("utf-8")) <= 256:
        raise HTTPException(status_code=503, detail=AUTH_CONFIGURATION_ERROR)
    if hmac.compare_digest(key.encode("utf-8"), _session_secret().encode("utf-8")):
        raise HTTPException(status_code=503, detail=AUTH_CONFIGURATION_ERROR)
    return key


def bootstrap_key_matches(candidate: str) -> bool:
    key = _bootstrap_key().encode("utf-8")
    supplied = candidate.encode("utf-8")
    if not 32 <= len(supplied) <= 256:
        return False
    return hmac.compare_digest(key, supplied)


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    if not 12 <= len(password) <= 128 or len(raw) > 512:
        raise ValueError("A senha deve ter entre 12 e 128 caracteres.")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(raw, salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=SCRYPT_KEY_LENGTH)
    encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${encode(salt)}${encode(digest)}"


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded or len(encoded) > 255:
        return False
    try:
        algorithm, n_text, r_text, p_text, salt_text, digest_text = encoded.split("$", 5)
        if algorithm != "scrypt" or (int(n_text), int(r_text), int(p_text)) != (SCRYPT_N, SCRYPT_R, SCRYPT_P):
            return False
        pad = lambda value: value + "=" * (-len(value) % 4)
        salt = base64.urlsafe_b64decode(pad(salt_text))
        expected = base64.urlsafe_b64decode(pad(digest_text))
        if len(salt) != 16 or len(expected) != SCRYPT_KEY_LENGTH:
            return False
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=SCRYPT_KEY_LENGTH)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError):
        return False


# Hash fixo para equalizar o custo das tentativas com username inexistente.
_DUMMY_PASSWORD_HASH = hash_password("Nexo-estoque-dummy-password")


def issue_session(user: Usuario) -> str:
    now = datetime.now(UTC)
    payload = {
        "iss": SESSION_ISSUER,
        "sub": user.open_id,
        "iat": now,
        "exp": now + SESSION_LIFETIME,
        "jti": secrets.token_urlsafe(18),
        "auth_method": "password",
    }
    return jwt.encode(payload, _session_secret(), algorithm="HS256")


def resolve_user(request: Request, db: Session, required: bool) -> Usuario | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
    if not token:
        if required:
            raise HTTPException(status_code=401, detail="Faça login para acessar esta área.")
        return None
    require_username_schema(db)
    try:
        claims = jwt.decode(
            token,
            _session_secret(),
            algorithms=["HS256"],
            issuer=SESSION_ISSUER,
            options={"require": ["exp", "iat", "iss", "sub", "jti"]},
        )
        if claims.get("auth_method") != "password" or not isinstance(claims.get("sub"), str):
            raise jwt.InvalidTokenError("Sessão sem identidade individual")
    except jwt.PyJWTError:
        if required:
            raise HTTPException(status_code=401, detail="Sessão inválida ou expirada. Entre novamente.") from None
        return None
    user = db.get(Usuario, claims["sub"])
    if user is None or not user.ativo:
        if required:
            raise HTTPException(status_code=401, detail="Conta inativa ou sessão inválida. Entre novamente.")
        return None
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Usuario:
    user = resolve_user(request, db, required=True)
    assert user is not None
    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> Usuario | None:
    return resolve_user(request, db, required=False)


def require_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem gerenciar usuários.")
    return user


def lock_user_administration(db: Session, actor_open_id: str | None = None) -> Usuario | None:
    require_username_schema(db, lock=True)
    if actor_open_id is None:
        return None
    actor = db.scalar(
        select(Usuario)
        .where(Usuario.open_id == actor_open_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if actor is None or not actor.ativo or actor.perfil != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores ativos podem gerenciar usuários.")
    return actor


def active_admin_count(db: Session, *, lock_rows: bool = False) -> int:
    statement = select(Usuario.open_id).where(Usuario.perfil == "admin", Usuario.ativo.is_(True))
    if lock_rows:
        statement = statement.with_for_update()
    return len(db.scalars(statement).all())


def has_active_admin(db: Session, *, lock_rows: bool = False) -> bool:
    return active_admin_count(db, lock_rows=lock_rows) > 0


def user_payload(user: Usuario | None) -> dict | None:
    if user is None:
        return None
    return {
        "open_id": user.open_id,
        "nome": user.nome,
        "username": user.username,
        "email": user.email,
        "perfil": user.perfil,
        "ativo": user.ativo,
    }
