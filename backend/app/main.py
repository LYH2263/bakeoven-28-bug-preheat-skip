from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.seed import seed_if_empty

# create_all does not alter existing tables; add new columns idempotently.
_COLUMN_MIGRATIONS = [
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS temp_profile VARCHAR(20) NOT NULL DEFAULT '中温'",
    "ALTER TABLE ovens ADD COLUMN IF NOT EXISTS preheat_min INTEGER NOT NULL DEFAULT 15",
    "ALTER TABLE batches ADD COLUMN IF NOT EXISTS preheat_min INTEGER NOT NULL DEFAULT 0",
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        for stmt in _COLUMN_MIGRATIONS:
            conn.execute(text(stmt))
    if settings.seed_on_empty:
        db = SessionLocal()
        try:
            seed_if_empty(db)
        finally:
            db.close()
    yield


app = FastAPI(title="BakeOven", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")
