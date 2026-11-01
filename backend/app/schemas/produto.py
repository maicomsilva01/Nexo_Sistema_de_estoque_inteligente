from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_uid(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = "".join(character for character in value.strip().upper() if character not in {" ", ":", "-"})
    return normalized or None


class ProdutoCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    nome: str = Field(min_length=1, max_length=140)
    categoria: str = Field(default="", max_length=80)
    unidade: str = Field(default="un", min_length=1, max_length=16)
    custo: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    estoque_minimo: int = Field(default=0, ge=0, le=2_000_000_000)
    estoque_inicial: int = Field(default=0, ge=0, le=2_000_000_000)
    rfid_uid: str | None = Field(default=None, max_length=80)

    @field_validator("sku", "nome", "unidade")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("O campo não pode ficar vazio.")
        return cleaned

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("rfid_uid")
    @classmethod
    def normalize_uid(cls, value: str | None) -> str | None:
        return _normalize_uid(value)


class ProdutoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=140)
    categoria: str | None = Field(default=None, max_length=80)
    unidade: str | None = Field(default=None, min_length=1, max_length=16)
    custo: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    estoque_minimo: int | None = Field(default=None, ge=0, le=2_000_000_000)
    rfid_uid: str | None = Field(default=None, max_length=80)
    ativo: bool | None = None

    @field_validator("nome", "unidade", mode="before")
    @classmethod
    def require_nonblank_text(cls, value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("O campo não pode ficar vazio ou nulo.")
        return value.strip()

    @field_validator("categoria", mode="before")
    @classmethod
    def strip_category(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("A categoria não pode ser nula.")
        return value.strip()

    @field_validator("estoque_minimo", "ativo", mode="before")
    @classmethod
    def reject_null_non_nullable(cls, value: object) -> object:
        if value is None:
            raise ValueError("O campo não pode ser nulo.")
        return value

    @field_validator("rfid_uid")
    @classmethod
    def normalize_uid(cls, value: str | None) -> str | None:
        return _normalize_uid(value)


class ProdutoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    nome: str
    categoria: str
    unidade: str
    custo: Decimal | None
    estoque_minimo: int
    estoque_inicial: int
    saldo: int
    rfid_uid: str | None
    ativo: bool
    demonstracao: bool
    atualizado_em: str
