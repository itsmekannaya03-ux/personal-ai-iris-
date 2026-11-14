from contextlib import asynccontextmanager
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import create_tables, check_database_connection, engine
from backend import models
from backend.routers import auth, profile, subscriptions, installer, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify live PostgreSQL connection on startup
    status = await check_database_connection()
    if status["connected"]:
        print(f"[DATABASE] Connected to PostgreSQL at {status['host']} (database: {status['database']}, user: {status.get('user')})")
        try:
            await create_tables()
            print("[DATABASE] Database tables verified successfully.")
        except Exception as e:
            print(f"[DATABASE ERROR] Table initialization failed: {e}")
    else:
        print(f"[DATABASE ERROR] Could NOT connect to PostgreSQL at {status['host']}: {status.get('error')}")
        print("[DATABASE ERROR] Startup warning: Database is unreachable. Check your network or credentials.")

    yield

    # Clean shutdown of connection pool
    try:
        await engine.dispose()
    except Exception:
        pass


app = FastAPI(
    title="IRIS AI API",
    version="0.1.0",
    lifespan=lifespan,
)

# Parse and sanitize configured origins: trim whitespace, quotes, trailing slashes
cors_origins = [
    origin.strip().strip("'\"").rstrip("/")
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

# Ensure the exact production Vercel frontend origin is explicitly allowed
if "https://personal-ai-iris.vercel.app" not in cors_origins:
    cors_origins.append("https://personal-ai-iris.vercel.app")

# Ensure localhost defaults
for dev_origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
    if dev_origin not in cors_origins:
        cors_origins.append(dev_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^https://personal-ai-iris.*\.vercel\.app$",
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
    with open("fastapi_error.log", "a", encoding="utf-8") as f:
        f.write(traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/health")
async def health():
    db_status = await check_database_connection()
    return {
        "status": "ok" if db_status["connected"] else "degraded",
        "database_connected": db_status["connected"],
        "database_host": db_status.get("host"),
        "version": "0.1.0",
    }
