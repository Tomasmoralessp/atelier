from pathlib import Path
import os

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker
from database.models import Base


DB_PATH = Path(
    os.environ.get("DB_PATH")
    or Path(__file__).resolve().parent.parent / "data" / "atelier.db"
)


engine = create_engine(f"sqlite:///{DB_PATH}")


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)


def get_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()
