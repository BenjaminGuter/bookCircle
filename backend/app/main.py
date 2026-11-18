import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.catalog.api.router import router as catalog_router
from app.shared.database import get_session
from app.shared.error_handlers import register_error_handlers

app = FastAPI(title="BookCircle")
register_error_handlers(app)

# Erlaubte Frontend-Adressen (Vite: 5173, CRA/Next: 3000), per Env überschreibbar.
# Mit dem Vite-Proxy (/api) wird CORS im Normalfall gar nicht gebraucht.
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],  # u. a. X-User-Id (Dev) bzw. später Authorization
)

app.include_router(catalog_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db(session: Session = Depends(get_session)):
    session.execute(text("SELECT 1"))
    return {"db": "ok"}