"""Fluxos de autenticação individual testados com SQLite isolado em memória."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base, get_db
from app.database.tables import VersaoSchema
from app.main import app
from app.models import Usuario
from app.services.auth_service import SESSION_COOKIE, active_admin_count, lock_user_administration, require_admin, verify_password

TEST_BOOTSTRAP_KEY = "bootstrap-key-" + "A" * 40
TEST_SESSION_SECRET = "session-secret-" + "B" * 40
REQUEST_HEADERS = {"X-Nexo-Request": "fetch"}
ADMIN_FORM = {
    "chave_bootstrap": TEST_BOOTSTRAP_KEY,
    "nome": "Admin Nexo",
    "username": "Turma2",
    "email": None,
    "senha": "Senha-forte-admin-2026",
    "origin": "https://estoque.example",
}


class IndividualAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite+pysqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.session_factory = sessionmaker(bind=cls.engine, autoflush=False, expire_on_commit=False)

        def override_get_db():
            db = cls.session_factory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.pop(get_db, None)
        cls.engine.dispose()

    def setUp(self) -> None:
        self.environment = patch.dict(
            os.environ,
            {
                "NEXO_ADMIN_BOOTSTRAP_KEY": TEST_BOOTSTRAP_KEY,
                "NEXO_SESSION_SECRET": TEST_SESSION_SECRET,
            },
            clear=False,
        )
        self.environment.start()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        with self.session_factory() as db:
            db.add(VersaoSchema(versao=2, descricao="Contas individuais para teste"))
            db.add(VersaoSchema(versao=3, descricao="Username para teste"))
            db.add(VersaoSchema(versao=4, descricao="Username obrigatório para teste"))
            db.commit()
        self.client = TestClient(app, base_url="https://testserver")

    def tearDown(self) -> None:
        self.client.close()
        self.environment.stop()

    def bootstrap(self, **overrides):
        data = {**ADMIN_FORM, **overrides}
        return self.client.post("/api/auth/bootstrap", json=data, headers=REQUEST_HEADERS)

    def create_admin(self) -> dict:
        response = self.bootstrap()
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["usuario"]

    def test_anonymous_status_protected_routes_and_bootstrap_flag(self) -> None:
        status = self.client.get("/api/auth/status")
        self.assertEqual(status.status_code, 200)
        self.assertFalse(status.json()["autenticado"])
        self.assertTrue(status.json()["bootstrap_disponivel"])
        self.assertEqual(self.client.get("/api/produtos").status_code, 401)
        self.assertEqual(self.client.get("/api/usuarios").status_code, 401)

    def test_bootstrap_fails_closed_without_completed_migration_marker(self) -> None:
        with self.session_factory() as db:
            marker = db.get(VersaoSchema, 4)
            assert marker is not None
            db.delete(marker)
            db.commit()
        response = self.bootstrap()
        self.assertEqual(response.status_code, 503)
        with self.session_factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(Usuario)), 0)

    def test_login_and_existing_sessions_fail_closed_without_v4_marker(self) -> None:
        admin = self.create_admin()
        with self.session_factory() as db:
            marker = db.get(VersaoSchema, 4)
            assert marker is not None
            db.delete(marker)
            db.commit()
        self.assertEqual(self.client.get("/api/produtos").status_code, 503)
        self.client.cookies.clear()
        status = self.client.get("/api/auth/status")
        self.assertFalse(status.json()["bootstrap_disponivel"])
        login = self.client.post(
            "/api/auth/login",
            json={"username": admin["username"], "senha": ADMIN_FORM["senha"], "origin": "https://estoque.example"},
            headers=REQUEST_HEADERS,
        )
        self.assertEqual(login.status_code, 503)

    def test_wrong_bootstrap_key_does_not_create_user_or_issue_cookie(self) -> None:
        response = self.bootstrap(chave_bootstrap="X" * 48)
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("set-cookie", response.headers)
        with self.session_factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(Usuario)), 0)

    def test_bootstrap_creates_individual_admin_and_closes_setup(self) -> None:
        response = self.bootstrap()
        self.assertEqual(response.status_code, 201, response.text)
        cookie = response.headers.get("set-cookie", "").lower()
        self.assertIn(f"{SESSION_COOKIE}=", cookie)
        self.assertIn("httponly", cookie)
        self.assertIn("secure", cookie)
        self.assertIn("samesite=none", cookie)
        self.assertFalse(self.client.get("/api/auth/status").json()["bootstrap_disponivel"])
        self.assertTrue(self.client.get("/api/auth/status").json()["autenticado"])
        with self.session_factory() as db:
            user = db.scalar(select(Usuario).where(Usuario.username == "turma2"))
            self.assertIsNotNone(user)
            assert user is not None
            self.assertEqual(user.perfil, "admin")
            self.assertTrue(user.ativo)
            assert user.password_hash is not None
            self.assertNotIn(ADMIN_FORM["senha"], user.password_hash)
            self.assertTrue(verify_password(ADMIN_FORM["senha"], user.password_hash))

    def test_bootstrap_claims_matching_passwordless_legacy_user_without_deleting_it(self) -> None:
        with self.session_factory() as db:
            legacy = Usuario(open_id="oauth-legacy-1", nome="Conta antiga", username="conta-antiga", email="admin@nexo.example", perfil="operador", password_hash=None, ativo=False)
            db.add(legacy)
            db.commit()
        response = self.bootstrap(email="admin@nexo.example")
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["usuario"]["open_id"], "oauth-legacy-1")
        with self.session_factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(Usuario)), 1)
            user = db.get(Usuario, "oauth-legacy-1")
            assert user is not None
            self.assertEqual(user.perfil, "admin")
            self.assertTrue(user.ativo)

    def test_bootstrap_is_disabled_after_an_admin_exists(self) -> None:
        self.create_admin()
        response = self.bootstrap(email="second@nexo.example")
        self.assertEqual(response.status_code, 409)
        self.assertFalse(self.client.get("/api/auth/status").json()["bootstrap_disponivel"])

    def test_login_uses_normalized_username_and_generic_error(self) -> None:
        self.create_admin()
        self.client.cookies.clear()
        success = self.client.post(
            "/api/auth/login",
            json={"username": " TURMA2 ", "senha": ADMIN_FORM["senha"], "origin": "https://estoque.example"},
            headers=REQUEST_HEADERS,
        )
        self.assertEqual(success.status_code, 200, success.text)
        self.assertTrue(success.json()["ok"])
        self.client.cookies.clear()
        wrong = self.client.post(
            "/api/auth/login",
            json={"username": "Turma2", "senha": "Senha-incorreta-2026", "origin": "https://estoque.example"},
            headers=REQUEST_HEADERS,
        )
        unknown = self.client.post(
            "/api/auth/login",
            json={"username": "nao-existe", "senha": "Senha-incorreta-2026", "origin": "https://estoque.example"},
            headers=REQUEST_HEADERS,
        )
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(unknown.status_code, 401)
        self.assertEqual(wrong.json()["detail"], unknown.json()["detail"])

    def test_old_shared_key_payload_is_not_accepted(self) -> None:
        response = self.client.post(
            "/api/auth/login",
            json={"access_key": "K" * 48, "origin": "https://estoque.example"},
            headers=REQUEST_HEADERS,
        )
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("set-cookie", response.headers)

    def test_account_management_requires_admin_and_supports_crud(self) -> None:
        self.create_admin()
        operator_response = self.client.post(
            "/api/usuarios",
            json={"nome": "Operador Teste", "username": "Operador-Teste", "senha": "Senha-operador-2026", "perfil": "operador"},
            headers=REQUEST_HEADERS,
        )
        self.assertEqual(operator_response.status_code, 201, operator_response.text)
        operator = operator_response.json()
        self.assertEqual(operator["username"], "operador-teste")
        duplicate = self.client.post(
            "/api/usuarios",
            json={"nome": "Duplicado", "username": "OPERADOR-TESTE", "senha": "Senha-operador-2026", "perfil": "operador"},
            headers=REQUEST_HEADERS,
        )
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(self.client.get("/api/usuarios").status_code, 200)
        updated = self.client.patch(
            f"/api/usuarios/{operator['open_id']}",
            json={"nome": "Operador Atualizado", "perfil": "admin", "senha": "Senha-operador-nova-2026"},
            headers=REQUEST_HEADERS,
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["perfil"], "admin")
        deactivated = self.client.delete(f"/api/usuarios/{operator['open_id']}", headers=REQUEST_HEADERS)
        self.assertEqual(deactivated.status_code, 204)
        users = self.client.get("/api/usuarios").json()
        operator_state = next(user["ativo"] for user in users if user["open_id"] == operator["open_id"])
        self.assertFalse(operator_state)

    def test_operator_cannot_access_management_or_change_roles(self) -> None:
        self.create_admin()
        operator_response = self.client.post(
            "/api/usuarios",
            json={"nome": "Operador", "username": "operador", "senha": "Senha-operador-2026", "perfil": "operador"},
            headers=REQUEST_HEADERS,
        )
        operator = operator_response.json()
        self.client.cookies.clear()
        login = self.client.post(
            "/api/auth/login",
            json={"username": "OPERADOR", "senha": "Senha-operador-2026", "origin": "https://estoque.example"},
            headers=REQUEST_HEADERS,
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.get("/api/usuarios").status_code, 403)
        denied = self.client.patch(f"/api/usuarios/{operator['open_id']}", json={"perfil": "admin"}, headers=REQUEST_HEADERS)
        self.assertEqual(denied.status_code, 403)

    def test_last_admin_cannot_be_demoted_or_deactivated(self) -> None:
        admin = self.create_admin()
        demote = self.client.patch(f"/api/usuarios/{admin['open_id']}", json={"perfil": "operador"}, headers=REQUEST_HEADERS)
        disable = self.client.delete(f"/api/usuarios/{admin['open_id']}", headers=REQUEST_HEADERS)
        self.assertEqual(demote.status_code, 409)
        self.assertEqual(disable.status_code, 409)

    def test_admin_mutations_share_lock_and_reject_stale_admin_actor(self) -> None:
        first_admin = self.create_admin()
        with patch("app.routes.usuarios.lock_user_administration", wraps=lock_user_administration) as admin_lock:
            created = self.client.post(
                "/api/usuarios",
                json={"nome": "Segundo admin", "username": "segundo-admin", "senha": "Senha-segundo-admin-2026", "perfil": "admin"},
                headers=REQUEST_HEADERS,
            )
            self.assertEqual(created.status_code, 201, created.text)
            second_admin = created.json()
            updated = self.client.patch(
                f"/api/usuarios/{second_admin['open_id']}",
                json={"nome": "Segundo admin atualizado"},
                headers=REQUEST_HEADERS,
            )
            self.assertEqual(updated.status_code, 200, updated.text)
            with self.session_factory() as db:
                stale_actor = db.get(Usuario, second_admin["open_id"])
                assert stale_actor is not None and stale_actor.perfil == "admin" and stale_actor.ativo
            deactivated = self.client.delete(f"/api/usuarios/{second_admin['open_id']}", headers=REQUEST_HEADERS)
            self.assertEqual(deactivated.status_code, 204)

            previous_override = app.dependency_overrides.get(require_admin)
            app.dependency_overrides[require_admin] = lambda: stale_actor
            try:
                stale_request = self.client.delete(f"/api/usuarios/{first_admin['open_id']}", headers=REQUEST_HEADERS)
            finally:
                if previous_override is None:
                    app.dependency_overrides.pop(require_admin, None)
                else:
                    app.dependency_overrides[require_admin] = previous_override
            self.assertEqual(stale_request.status_code, 403)
            self.assertEqual(admin_lock.call_count, 4)

        with self.session_factory() as db:
            self.assertEqual(active_admin_count(db), 1)

    def test_inactive_account_is_denied_even_with_an_old_session(self) -> None:
        admin = self.create_admin()
        self.client.cookies.clear()
        self.client.post(
            "/api/auth/login",
            json={"username": admin["username"], "senha": ADMIN_FORM["senha"], "origin": "https://estoque.example"},
            headers=REQUEST_HEADERS,
        )
        with self.session_factory() as db:
            user = db.get(Usuario, admin["open_id"])
            assert user is not None
            user.ativo = False
            db.commit()
        self.assertFalse(self.client.get("/api/auth/status").json()["autenticado"])
        self.assertEqual(self.client.get("/api/produtos").status_code, 401)

    def test_localhost_uses_lax_cookie_without_secure_attribute(self) -> None:
        response = self.bootstrap(origin="http://localhost:3000")
        self.assertEqual(response.status_code, 201, response.text)
        cookie = response.headers.get("set-cookie", "").lower()
        self.assertIn("samesite=lax", cookie)
        self.assertNotIn("; secure", cookie)

    def test_missing_or_reused_secrets_fail_closed(self) -> None:
        with patch.dict(os.environ, {"NEXO_SESSION_SECRET": "", "NEXO_ADMIN_BOOTSTRAP_KEY": ""}):
            missing = self.bootstrap()
        self.assertEqual(missing.status_code, 503)
        with patch.dict(os.environ, {"NEXO_SESSION_SECRET": "Z" * 40, "NEXO_ADMIN_BOOTSTRAP_KEY": "Z" * 40}):
            reused = self.bootstrap()
        self.assertEqual(reused.status_code, 503)
        self.assertNotIn(TEST_SESSION_SECRET, missing.text)

    def test_mutations_without_request_marker_are_rejected(self) -> None:
        response = self.client.post("/api/auth/bootstrap", json=ADMIN_FORM)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("set-cookie", response.headers)


if __name__ == "__main__":
    unittest.main()
