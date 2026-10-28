"""FastAPI application - Nusantara Core + Hermes."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.routes import router as api_router
from app.exceptions import register_exception_handlers

UI_FILE = Path(__file__).parent / "ui" / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Nusantara Core + Hermes API",
    description="AI Core Engine and Agent/Orchestrator API",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/", include_in_schema=False)
@app.get("/ui", include_in_schema=False)
async def dashboard():
    return FileResponse(UI_FILE)
