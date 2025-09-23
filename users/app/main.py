from fastapi import FastAPI, HTTPException, Depends
import os
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .db import engine, Base, get_session
from .routers import users as users_router
from .routers import auth as auth_router
from .routers import profile as profile_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Note: Database migrations should be run separately using Alembic
    # This ensures proper schema versioning in production environments
    yield
    await engine.dispose()

app = FastAPI(title="Users API", version="0.2.0", lifespan=lifespan)

@app.get("/")
def read_root():
    return {
        "message": "Hello from FastAPI on Kubernetes! updated",
        "version": app.version,
        "env": os.getenv("APP_ENV", "dev"),
    }

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.get("/readyz")
async def ready():
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="db not ready")

# Routers
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(profile_router.router)
