from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        Index("uq_usuarios_email", "email", unique=True),
        Index("uq_usuarios_username", "username", unique=True),
    )

    open_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    username: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    perfil: Mapped[str] = mapped_column(String(40), default="operador", nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
