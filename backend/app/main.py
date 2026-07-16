from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import jobs, upload, websocket
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(debug=settings.debug)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Separação de stems musicais com IA — engines trocáveis (Demucs, MDX-Net) "
    "e análise musical (BPM, tonalidade, acordes, loudness).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allow_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(jobs.router)
app.include_router(websocket.router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
