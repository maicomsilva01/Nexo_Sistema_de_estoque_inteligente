from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, SecretStr, field_validator

PerfilUsuario = Literal["admin", "operador"]
EMAIL_SHAPE = re.compile(r"^[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+$")
USERNAME_SHAPE = re.compile(r"^[A-Za-z0-9._-]{3,32}$")


def normalized_username(value: str) -> str:
    candidate = value.strip()
    if not USERNAME_SHAPE.fullmatch(candidate):
        raise ValueError("Use um nome de usuário de 3 a 32 caracteres: letras, números, ponto, hífen ou sublinhado.")
    return candidate.lower()


def normalized_email(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    candidate = value.strip().lower()
    if len(candidate) > 254 or not EMAIL_SHAPE.fullmatch(candidate):
        raise ValueError("Informe um e-mail válido ou deixe o campo vazio.")
    return candidate


class PasswordLogin(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    senha: SecretStr = Field(min_length=12, max_length=128)
    origin: str = Field(min_length=1, max_length=500)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return normalized_username(value)


class BootstrapAdmin(BaseModel):
    chave_bootstrap: SecretStr = Field(min_length=32, max_length=256)
    nome: str = Field(min_length=2, max_length=160)
    username: str = Field(min_length=3, max_length=32)
    email: str | None = Field(default=None, max_length=254)
    senha: SecretStr = Field(min_length=12, max_length=128)
    origin: str = Field(min_length=1, max_length=500)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return normalized_username(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return normalized_email(value)

    @field_validator("nome")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Informe um nome com pelo menos 2 caracteres.")
        return cleaned


class UserOut(BaseModel):
    open_id: str
    nome: str
    username: str
    email: str | None
    perfil: str
    ativo: bool


class AuthStatusOut(BaseModel):
    autenticado: bool
    usuario: UserOut | None
    bootstrap_disponivel: bool


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=160)
    username: str = Field(min_length=3, max_length=32)
    email: str | None = Field(default=None, max_length=254)
    senha: SecretStr = Field(min_length=12, max_length=128)
    perfil: PerfilUsuario = "operador"

    @field_validator("nome")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Informe um nome com pelo menos 2 caracteres.")
        return cleaned

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return normalized_username(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return normalized_email(value)


class UsuarioUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=160)
    username: str | None = Field(default=None, min_length=3, max_length=32)
    email: str | None = Field(default=None, max_length=254)
    senha: SecretStr | None = Field(default=None, min_length=12, max_length=128)
    perfil: PerfilUsuario | None = None
    ativo: bool | None = None

    @field_validator("nome")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Informe um nome com pelo menos 2 caracteres.")
        return cleaned

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        return normalized_username(value) if value is not None else None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return normalized_email(value)
