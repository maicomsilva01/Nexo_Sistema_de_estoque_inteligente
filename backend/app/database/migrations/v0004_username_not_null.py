"""Endurece usernames preenchidos sem remover contas nem histórico."""

from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

revision = 4
description = "Username obrigatório e autenticação condicionada ao schema atual"


def upgrade(connection: Connection) -> None:
    columns = {column["name"] for column in inspect(connection).get_columns("usuarios")}
    if "username" not in columns:
        raise RuntimeError("A migração v3 deve ser aplicada antes da v4 de usernames.")

    missing = connection.execute(
        text("SELECT COUNT(*) FROM usuarios WHERE username IS NULL OR TRIM(username) = ''")
    ).scalar_one()
    if missing:
        raise RuntimeError("A migração v4 não pode prosseguir: há contas sem username após o backfill v3.")

    indexes = inspect(connection).get_indexes("usuarios")
    if not any(index.get("name") == "uq_usuarios_username" and index.get("unique") for index in indexes):
        raise RuntimeError("A migração v3 deve criar a unicidade de username antes da v4.")

    dialect = connection.dialect.name
    if dialect == "mysql":
        connection.execute(text("ALTER TABLE usuarios MODIFY COLUMN username VARCHAR(32) NOT NULL"))
    elif dialect == "sqlite":
        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS trg_usuarios_username_required_insert
            BEFORE INSERT ON usuarios
            FOR EACH ROW
            WHEN NEW.username IS NULL OR TRIM(NEW.username) = ''
            BEGIN
                SELECT RAISE(ABORT, 'username required');
            END
        """))
        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS trg_usuarios_username_required_update
            BEFORE UPDATE OF username ON usuarios
            FOR EACH ROW
            WHEN NEW.username IS NULL OR TRIM(NEW.username) = ''
            BEGIN
                SELECT RAISE(ABORT, 'username required');
            END
        """))
    else:
        raise RuntimeError(f"A migração v4 não suporta o dialeto {dialect!r}.")
