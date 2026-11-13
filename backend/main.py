from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import traceback
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import create_tables
from backend import models
from backend.routers import auth, profile, subscriptions, installer, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_tables()
    except Exception as e:
        print(f"[WARNING] Database connection failed ({e}). Running without live PostgreSQL connection.")
    yield


app = FastAPI(
    title="IRIS AI API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(subscriptions.router)
app.include_router(installer.router)
app.include_router(webhooks.router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    with open("fastapi_error.log", "a") as f:
        f.write(traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
