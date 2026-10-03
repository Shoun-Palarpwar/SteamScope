"""
STEAMSCOPE API

Run with:
    uvicorn main:app --reload

Then visit http://127.0.0.1:8000/docs for interactive API docs
(FastAPI generates this automatically).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import games, analytics, users

app = FastAPI(
    title="SteamScope API",
    description="Database-driven game library & Steam ecosystem analytics platform.",
    version="0.1.0",
)

# Open CORS for local frontend dev. Tighten allow_origins to your
# actual frontend URL before deploying anywhere real.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router, prefix="/games", tags=["games"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/")
def root():
    return {"status": "ok", "service": "SteamScope API"}
