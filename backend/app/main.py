import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mysql.connector import Error
from .db import start_pool, get_cursor
from .schemas import Health, Ready
from .routers import games, users, analytics, collections, discovery, rankings

@asynccontextmanager
async def lifespan(app):
    start_pool()
    yield

app = FastAPI(title="SteamScope API", version="0.3.0", lifespan=lifespan,
    description="Real Steam catalog with editable simulated demo profiles. No authentication; run locally.")
app.add_middleware(CORSMiddleware,
    allow_origins=os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_methods=["GET", "PUT", "PATCH", "DELETE"], allow_headers=["Content-Type"])
# Register static routes before routes with dynamic identifiers.
for module, prefix, tag in [(collections,"/users","collections"),
    (discovery,"","discovery"),(rankings,"/analytics","rankings"),
    (games,"/games","games"),(users,"/users","users"),(analytics,"/analytics","analytics")]:
    app.include_router(module.router, prefix=prefix, tags=[tag])

@app.exception_handler(Error)
async def database_error(request: Request, exc: Error):
    logging.getLogger(__name__).exception("Database operation failed", exc_info=exc)
    return JSONResponse(status_code=503, content={"detail":"Database operation failed; check server logs."})

@app.get("/health", response_model=Health)
@app.get("/", response_model=Health)
def health():
    return {"status":"ok", "service":"SteamScope API", "demo_mode":True}

@app.get("/health/ready", response_model=Ready)
def ready():
    with get_cursor() as cur:
        cur.execute("SELECT is_favorite FROM `library` LIMIT 0")
    return {"status":"ready", "database":"connected"}
