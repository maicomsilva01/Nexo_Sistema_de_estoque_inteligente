"""Adiciona autenticação individual sem apagar usuários ou histórico."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

revision = 2
description = "Contas individuais, hash de senha, estado ativo e e-mail único"


def upgrade(connection: Connection) -> None:
    columns = {column["name"] for column in inspect(connection).get_columns("usuarios")}
    if "password_hash" not in columns:
        connection.execute(text("ALTER TABLE usuarios ADD COLUMN password_hash VARCHAR(255) NULL"))
    if "ativo" not in columns:
        connection.execute(text("ALTER TABLE usuarios ADD COLUMN ativo BOOLEAN NOT NULL DEFAULT 0"))

    # Contas anteriores não tinham senha própria: preservamos os registros, mas não concedemos acesso.
    connection.execute(text("UPDATE usuarios SET ativo = 0 WHERE password_hash IS NULL"))

    indexes = inspect(connection).get_indexes("usuarios")
    if not any(index.get("name") == "uq_usuarios_email" and index.get("unique") for index in indexes):
        connection.execute(text("CREATE UNIQUE INDEX uq_usuarios_email ON usuarios (email)"))
