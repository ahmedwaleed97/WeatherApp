from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine

app = FastAPI(title="Weather API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/db-health")
def db_health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"db": "connected"}