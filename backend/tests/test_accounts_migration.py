"""Verifica migrações aditivas de contas em SQLite isolado."""

from __future__ import annotations

import unittest

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.database.migrations.v0002_contas_individuais import upgrade as upgrade_accounts
from app.database.migrations.v0003_username_login import upgrade as upgrade_usernames
from app.database.migrations.v0004_username_not_null import upgrade as upgrade_required_usernames


class AccountMigrationTests(unittest.TestCase):
    def test_migrations_preserve_legacy_accounts_and_enforce_unique_required_usernames(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:")
        try:
            with engine.begin() as connection:
                connection.execute(text(
                    "CREATE TABLE usuarios (open_id VARCHAR(160) PRIMARY KEY, nome VARCHAR(160) NOT NULL, "
                    "email VARCHAR(254), perfil VARCHAR(40) NOT NULL, criado_em DATETIME NOT NULL)"
                ))
                connection.execute(text("CREATE INDEX ix_usuarios_email ON usuarios (email)"))
                connection.execute(text(
                    "INSERT INTO usuarios (open_id, nome, email, perfil, criado_em) VALUES "
                    "('legacy-1', 'Conta legada 1', 'turma2@um.exemplo', 'operador', CURRENT_TIMESTAMP), "
                    "('legacy-2', 'Conta legada 2', 'TURMA2@dois.exemplo', 'operador', CURRENT_TIMESTAMP), "
                    "('legacy-3', 'Conta sem e-mail', NULL, 'operador', CURRENT_TIMESTAMP)"
                ))
                upgrade_accounts(connection)
                upgrade_usernames(connection)
                upgrade_required_usernames(connection)
                upgrade_required_usernames(connection)

                rows = connection.execute(
                    text("SELECT open_id, nome, email, username, password_hash, ativo FROM usuarios ORDER BY open_id")
                ).mappings().all()
                self.assertEqual([row["username"] for row in rows], ["turma2", "turma2-2", "conta-sem-e-mail"])
                self.assertEqual(rows[0]["email"], "turma2@um.exemplo")
                self.assertIsNone(rows[2]["email"])
                self.assertTrue(all(row["password_hash"] is None for row in rows))
                self.assertTrue(all(not bool(row["ativo"]) for row in rows))
                self.assertEqual(len(rows), 3)

                indexes = inspect(connection).get_indexes("usuarios")
                unique_email = [index for index in indexes if index.get("name") == "uq_usuarios_email"]
                unique_username = [index for index in indexes if index.get("name") == "uq_usuarios_username"]
                self.assertEqual(len(unique_email), 1)
                self.assertTrue(unique_email[0]["unique"])
                self.assertEqual(len(unique_username), 1)
                self.assertTrue(unique_username[0]["unique"])

            for index, invalid_username in enumerate((None, "", "   "), start=1):
                with self.assertRaises(IntegrityError):
                    with engine.begin() as connection:
                        connection.execute(
                            text(
                                "INSERT INTO usuarios (open_id, nome, username, email, perfil, criado_em) "
                                "VALUES (:open_id, 'Conta inválida', :username, NULL, 'operador', CURRENT_TIMESTAMP)"
                            ),
                            {"open_id": f"invalid-{index}", "username": invalid_username},
                        )
                with self.assertRaises(IntegrityError):
                    with engine.begin() as connection:
                        connection.execute(
                            text("UPDATE usuarios SET username = :username WHERE open_id = 'legacy-1'"),
                            {"username": invalid_username},
                        )
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
