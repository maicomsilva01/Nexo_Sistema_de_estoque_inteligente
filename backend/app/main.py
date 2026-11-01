from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database.tables import initialize_database
from app.routes import auth, estoque, movimentacoes, previsoes, produtos, usuarios

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Nexo Estoque API",
    description="API de produtos, movimentações rastreáveis, saldo, alertas, previsões, RFID e contas individuais.",
    version="0.2.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def require_same_origin_marker(request, call_next):
    if request.url.path.startswith("/api/") and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if request.headers.get("x-nexo-request") != "fetch":
            return JSONResponse(status_code=403, content={"detail": "Requisição de alteração não permitida."})
    return await call_next(request)


for route_module in (auth, usuarios, produtos, movimentacoes, estoque, previsoes):
    app.include_router(route_module.router)


@app.get("/_app/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nexo-estoque"}


if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/", include_in_schema=False)
def home():
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"service": "Nexo Estoque API", "health": "/_app/health", "message": "O frontend é servido pelo Vite durante o desenvolvimento."}


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    if full_path.startswith(("api/", "_app/")):
        raise HTTPException(status_code=404, detail="Rota não encontrada.")
    if not FRONTEND_DIST.exists():
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")
    candidate = (FRONTEND_DIST / full_path).resolve()
    if candidate.is_relative_to(FRONTEND_DIST.resolve()) and candidate.is_file():
        return FileResponse(candidate)
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    raise HTTPException(status_code=404, detail="Página não encontrada.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "3000")))
