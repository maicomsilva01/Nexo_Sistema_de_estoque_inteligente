from __future__ import annotations

from typing import Literal, TypedDict
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import Usuario
from app.schemas.auth import BootstrapAdmin, PasswordLogin, normalized_email, normalized_username
from app.services.auth_service import (
    SESSION_COOKIE,
    SESSION_LIFETIME_SECONDS,
    _DUMMY_PASSWORD_HASH,
    _session_secret,
    bootstrap_key_matches,
    get_optional_user,
    has_active_admin,
    hash_password,
    issue_session,
    lock_user_administration,
    require_username_schema,
    username_schema_ready,
    user_payload,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["autenticação"])


class CookiePolicy(TypedDict):
    secure: bool
    samesite: Literal["none", "lax"]


def _valid_app_origin(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="Origem do aplicativo inválida.")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise HTTPException(status_code=400, detail="A origem deve conter somente protocolo e domínio.")
    is_local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not is_local:
        raise HTTPException(status_code=400, detail="O acesso exige HTTPS fora do ambiente local.")
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def _cookie_policy(public_origin: str) -> CookiePolicy:
    secure = urlsplit(public_origin).scheme == "https"
    return {"secure": secure, "samesite": "none" if secure else "lax"}


def _set_session(response: Response, user: Usuario, origin: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        issue_session(user),
        max_age=SESSION_LIFETIME_SECONDS,
        path="/",
        httponly=True,
        **_cookie_policy(origin),
    )


@router.get("/status")
def auth_status(db: Session = Depends(get_db), user: Usuario | None = Depends(get_optional_user)) -> dict:
    return {
        "autenticado": user is not None,
        "usuario": user_payload(user),
        "bootstrap_disponivel": username_schema_ready(db) and not has_active_admin(db),
    }


@router.post("/bootstrap", status_code=201)
def bootstrap_admin(payload: BootstrapAdmin, response: Response, db: Session = Depends(get_db)) -> dict:
    _session_secret()
    origin = _valid_app_origin(payload.origin)
    lock_user_administration(db)
    if has_active_admin(db, lock_rows=True):
        raise HTTPException(status_code=409, detail="O primeiro administrador já foi configurado.")
    if not bootstrap_key_matches(payload.chave_bootstrap.get_secret_value()):
        raise HTTPException(status_code=401, detail="Chave de primeiro acesso inválida.")

    username = normalized_username(payload.username)
    email = normalized_email(payload.email)
    user_by_username = db.scalar(select(Usuario).where(func.lower(func.trim(Usuario.username)) == username).limit(1))
    user_by_email = None
    if email is not None:
        user_by_email = db.scalar(select(Usuario).where(func.lower(func.trim(Usuario.email)) == email).limit(1))
    if user_by_username is not None and user_by_email is not None and user_by_username.open_id != user_by_email.open_id:
        raise HTTPException(status_code=409, detail="O nome de usuário e o e-mail já pertencem a contas diferentes.")
    user = user_by_email or user_by_username
    if user is not None:
        if user.password_hash is not None:
            raise HTTPException(status_code=409, detail="Este nome de usuário ou e-mail já está associado a uma conta.")
        user.nome = " ".join(payload.nome.split())
        user.username = username
        user.email = email
        user.password_hash = hash_password(payload.senha.get_secret_value())
        user.perfil = "admin"
        user.ativo = True
    else:
        user = Usuario(
            open_id=f"usr_{uuid4().hex}",
            nome=" ".join(payload.nome.split()),
            username=username,
            email=email,
            perfil="admin",
            password_hash=hash_password(payload.senha.get_secret_value()),
            ativo=True,
        )
        db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível criar a conta inicial. Verifique se o nome de usuário ou e-mail já está em uso.") from None
    db.refresh(user)
    _set_session(response, user, origin)
    return {"ok": True, "usuario": user_payload(user)}


@router.post("/login")
def password_login(payload: PasswordLogin, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        raise HTTPException(status_code=415, detail="O login exige uma requisição JSON.")
    origin = _valid_app_origin(payload.origin)
    _session_secret()
    require_username_schema(db)
    username = normalized_username(payload.username)
    user = db.scalar(select(Usuario).where(func.lower(func.trim(Usuario.username)) == username).limit(1))
    password = payload.senha.get_secret_value()
    valid_password = verify_password(password, user.password_hash if user is not None else _DUMMY_PASSWORD_HASH)
    if user is None or not user.ativo or user.password_hash is None or not valid_password:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")
    _set_session(response, user, origin)
    return {"ok": True, "usuario": user_payload(user)}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict:
    public_origin = request.headers.get("origin", "")
    if public_origin:
        public_origin = _valid_app_origin(public_origin)
    else:
        public_origin = "https://preview.invalid"
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        httponly=True,
        **_cookie_policy(public_origin),
    )
    return {"ok": True}
