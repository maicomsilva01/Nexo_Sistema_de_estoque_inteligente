from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Movimentacao(Base):
    __tablename__ = "movimentacoes"
    __table_args__ = (Index("ix_movimentacoes_produto_data", "produto_id", "criado_em"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id", ondelete="RESTRICT"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(16), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    usuario_open_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    usuario_nome: Mapped[str | None] = mapped_column(String(160), nullable=True)
    origem: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    produto: Mapped["Produto"] = relationship(back_populates="movimentacoes")
