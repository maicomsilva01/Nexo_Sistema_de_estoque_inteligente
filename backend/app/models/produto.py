from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(140), index=True, nullable=False)
    categoria: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    unidade: Mapped[str] = mapped_column(String(16), default="un", nullable=False)
    custo: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    estoque_minimo: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estoque_inicial: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rfid_uid: Mapped[str | None] = mapped_column(String(80), unique=True, index=True, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    demonstracao: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    movimentacoes: Mapped[list["Movimentacao"]] = relationship(back_populates="produto", cascade="all, delete-orphan")
