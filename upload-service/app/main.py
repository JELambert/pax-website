"""PAX Upload Service — FastAPI application."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .config import get_settings
from .routes import auth_routes, upload, status

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="PAX Upload Service",
    description="Upload PAX packs to the marketplace",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting (limiter instance lives on the upload router)
app.state.limiter = upload.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.main_site_url, settings.base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_routes.router)
app.include_router(upload.router)
app.include_router(status.router)


@app.get("/")
async def index():
    """Serve the upload UI."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


# Serve static assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
