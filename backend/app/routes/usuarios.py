from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import Usuario
from app.schemas.auth import UsuarioCreate, UsuarioUpdate, normalized_email, normalized_username
from app.services.auth_service import active_admin_count, hash_password, lock_user_administration, require_admin

router = APIRouter(prefix="/api/usuarios", tags=["usuários"])


def _admin_count(db: Session) -> int:
    return active_admin_count(db, lock_rows=True)


def _serialize(user: Usuario) -> dict[str, str | bool | None]:
    return {
        "open_id": user.open_id,
        "nome": user.nome,
        "username": user.username,
        "email": user.email,
        "perfil": user.perfil,
        "ativo": user.ativo,
    }


def _protect_last_admin(db: Session, target: Usuario, next_profile: str, next_active: bool) -> None:
    if target.perfil == "admin" and target.ativo and (next_profile != "admin" or not next_active) and _admin_count(db) <= 1:
        raise HTTPException(status_code=409, detail="Não é possível desativar ou rebaixar o último administrador ativo.")


@router.get("")
def list_users(db: Session = Depends(get_db), _admin: Usuario = Depends(require_admin)) -> list[dict]:
    users = db.scalars(select(Usuario).order_by(func.lower(Usuario.username), func.lower(Usuario.nome))).all()
    return [_serialize(user) for user in users]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(payload: UsuarioCreate, db: Session = Depends(get_db), _admin: Usuario = Depends(require_admin)) -> dict:
    user = Usuario(
        open_id=f"usr_{uuid4().hex}",
        nome=payload.nome,
        username=normalized_username(payload.username),
        email=normalized_email(payload.email),
        perfil=payload.perfil,
        password_hash=hash_password(payload.senha.get_secret_value()),
        ativo=True,
    )
    lock_user_administration(db, _admin.open_id)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma conta com este nome de usuário ou e-mail.") from None
    db.refresh(user)
    return _serialize(user)


@router.patch("/{open_id}")
def update_user(open_id: str, payload: UsuarioUpdate, db: Session = Depends(get_db), actor: Usuario = Depends(require_admin)) -> dict:
    lock_user_administration(db, actor.open_id)
    user = db.get(Usuario, open_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")
    changes = payload.model_dump(exclude_unset=True)
    changes = {key: value for key, value in changes.items() if value is not None or key == "email"}
    if "username" in changes:
        changes["username"] = normalized_username(str(changes["username"]))
    if "email" in changes:
        changes["email"] = normalized_email(changes["email"])
    next_profile = changes.get("perfil", user.perfil) or user.perfil
    next_active = bool(changes.get("ativo", user.ativo))
    _protect_last_admin(db, user, next_profile, next_active)
    if actor.open_id == user.open_id and user.perfil == "admin" and (next_profile != "admin" or not next_active):
        raise HTTPException(status_code=409, detail="Não é possível rebaixar ou desativar a própria conta nesta sessão.")

    password = changes.pop("senha", None)
    if password is not None:
        changes["password_hash"] = hash_password(password.get_secret_value())
    for field, value in changes.items():
        setattr(user, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma conta com este nome de usuário ou e-mail.") from None
    db.refresh(user)
    return _serialize(user)


@router.delete("/{open_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(open_id: str, response: Response, db: Session = Depends(get_db), actor: Usuario = Depends(require_admin)) -> Response:
    lock_user_administration(db, actor.open_id)
    user = db.get(Usuario, open_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")
    if actor.open_id == user.open_id:
        raise HTTPException(status_code=409, detail="Não é possível desativar a própria conta nesta sessão.")
    _protect_last_admin(db, user, user.perfil, False)
    user.ativo = False
    db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
