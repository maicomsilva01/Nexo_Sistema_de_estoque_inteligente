from __future__ import annotations

import json
import os
import ssl
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def _engine_parameters() -> tuple[str, dict]:
    raw = os.getenv("DATABASE_URL", "").strip()
    if not raw:
        raise RuntimeError("DATABASE_URL não está configurada. Configure a conexão gerenciada do projeto.")
    url = make_url(raw)
    if url.drivername == "mysql":
        url = url.set(drivername="mysql+pymysql")
    query = dict(url.query)
    tls_option = query.pop("ssl", None)
    connect_args: dict = {"connect_timeout": 10}
    if tls_option:
        try:
            options = json.loads(tls_option) if isinstance(tls_option, str) else tls_option
        except json.JSONDecodeError as exc:
            raise RuntimeError("A opção TLS do DATABASE_URL precisa ser JSON válido.") from exc
        if not isinstance(options, dict):
            raise RuntimeError("A opção TLS do DATABASE_URL precisa ser um objeto JSON.")
        context = ssl.create_default_context(cafile=options.get("ca"))
        if options.get("cert"):
            context.load_cert_chain(options["cert"], options.get("key"))
        if options.get("cipher"):
            context.set_ciphers(options["cipher"])
        if options.get("rejectUnauthorized") is False:
            # Compatibilidade explícita com a política fornecida no DSN gerenciado;
            # o canal continua criptografado, mas não valida o certificado do servidor.
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = context
    url = url.set(query=query)
    return url.render_as_string(hide_password=False), connect_args


_DATABASE_URL, _CONNECT_ARGS = _engine_parameters()


class Base(DeclarativeBase):
    pass


engine = create_engine(
    _DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args=_CONNECT_ARGS,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
