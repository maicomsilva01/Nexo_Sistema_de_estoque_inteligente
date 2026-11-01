from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

TipoMovimentacao = Literal["entrada", "saida", "ajuste"]
MAX_QUANTITY = 2_000_000_000


class MovimentacaoCreate(BaseModel):
    produto_id: int = Field(gt=0)
    tipo: TipoMovimentacao
    quantidade: int = Field(ge=-MAX_QUANTITY, le=MAX_QUANTITY)
    motivo: str = Field(default="", max_length=240)

    @model_validator(mode="after")
    def validate_quantity(self) -> "MovimentacaoCreate":
        if self.tipo in {"entrada", "saida"} and self.quantidade <= 0:
            raise ValueError("Entradas e saídas devem ter quantidade maior que zero.")
        if self.tipo == "ajuste" and self.quantidade == 0:
            raise ValueError("O ajuste precisa ter uma quantidade diferente de zero.")
        return self

    @field_validator("motivo")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()


class LeituraRfid(BaseModel):
    uid: str = Field(min_length=1, max_length=80)
    tipo: Literal["entrada", "saida", "ajuste"] = "entrada"
    quantidade: int = Field(default=1, ge=1, le=MAX_QUANTITY)

    @field_validator("uid")
    @classmethod
    def normalize_uid(cls, value: str) -> str:
        normalized = "".join(character for character in value.strip().upper() if character not in {" ", ":", "-"})
        if not normalized:
            raise ValueError("UID da tag é obrigatória.")
        return normalized
