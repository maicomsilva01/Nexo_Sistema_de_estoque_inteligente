"""Migração inicial: cria somente tabelas ausentes, sem apagar dados existentes."""

from sqlalchemy.engine import Connection

from app.database.connection import Base
from app.models import Movimentacao, Produto, Usuario  # noqa: F401 — registra metadados ORM

revision = 1
description = "Esquema inicial de estoque, usuários e movimentações"


def upgrade(connection: Connection) -> None:
    Base.metadata.create_all(bind=connection)
