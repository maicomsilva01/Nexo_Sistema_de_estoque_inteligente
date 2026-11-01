"""Adiciona nomes de usuário únicos sem remover contas nem e-mails existentes."""

from __future__ import annotations

import re

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

revision = 3
description = "Login por username único com e-mail opcional"


def _username_base(value: str | None) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", (value or "").strip()).strip("._-").lower()
    if not base:
        base = "usuario"
    if len(base) < 3:
        base = f"{base}-usr"
    return base[:32]


def upgrade(connection: Connection) -> None:
    columns = {column["name"] for column in inspect(connection).get_columns("usuarios")}
    if "username" not in columns:
        connection.execute(text("ALTER TABLE usuarios ADD COLUMN username VARCHAR(32) NULL"))

    rows = connection.execute(
        text("SELECT open_id, nome, email, username FROM usuarios ORDER BY open_id")
    ).mappings().all()
    used: set[str] = set()
    for row in rows:
        username = row["username"]
        if username:
            source = str(username)
        elif row["email"]:
            source = str(row["email"]).split("@", 1)[0]
        else:
            source = str(row["nome"] or "usuario")

        base = _username_base(source)
        candidate = base
        suffix_number = 2
        while candidate in used:
            suffix = f"-{suffix_number}"
            candidate = f"{base[:32 - len(suffix)]}{suffix}"
            suffix_number += 1
        used.add(candidate)
        if username != candidate:
            connection.execute(
                text("UPDATE usuarios SET username = :username WHERE open_id = :open_id"),
                {"username": candidate, "open_id": row["open_id"]},
            )

    indexes = inspect(connection).get_indexes("usuarios")
    if not any(index.get("name") == "uq_usuarios_username" and index.get("unique") for index in indexes):
        connection.execute(text("CREATE UNIQUE INDEX uq_usuarios_username ON usuarios (username)"))
