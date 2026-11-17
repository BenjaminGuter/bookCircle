import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Die .env im Repo-Root laden (backend/app/shared/database.py -> parents[3] = Repo-Root).
# Bereits gesetzte Umgebungsvariablen haben Vorrang, ohne .env passiert nichts.
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

# Der Default erlaubt den Import auch ohne Konfiguration (z. B. in Tests);
# create_engine verbindet erst bei der ersten Query.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://bookcircle:change_me@localhost:5432/bookcircle"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_session():
    """FastAPI-Dependency: eine Session pro Request, Commit/Rollback hier."""
    with SessionLocal() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise