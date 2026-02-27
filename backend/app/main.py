from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import startup_db, shutdown_db
from app.core.middleware import LoggingMiddleware, SecurityHeadersMiddleware

from app.modules.auth.router import router as auth_router
from app.modules.empresas.router import router as empresas_router
from app.modules.tributario.f29.router import router as f29_router
from app.modules.tributario.dj.router import router as dj_router
from app.modules.tributario.situacion.router import router as situacion_router
from app.modules.ia.router import router as ia_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_db()
    yield
    await shutdown_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)

# Routers
app.include_router(auth_router, prefix="/api")
app.include_router(empresas_router, prefix="/api")
app.include_router(f29_router, prefix="/api")
app.include_router(dj_router, prefix="/api")
app.include_router(situacion_router, prefix="/api")
app.include_router(ia_router, prefix="/api")


@app.get("/api/salud")
async def health():
    return {"estado": "OK", "version": settings.APP_VERSION}
