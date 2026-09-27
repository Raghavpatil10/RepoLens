from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.analyze import router as analyze_router

app = FastAPI(
    title="RepoLens API",
    description="Paste a public GitHub repo URL, get back a structured technical audit.",
    version="0.1.0",
)

# Wide-open CORS is fine for local development against the static frontend.
# Tighten this (specific origins) before deploying anywhere public.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)
@app.get("/")
def read_root() -> dict:
    return {"message": "Welcome to the RepoLens API!"}


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
