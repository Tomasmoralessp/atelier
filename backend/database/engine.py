from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

import settings
from database.models import Base

settings.ensure_data_dirs()

engine = create_engine(
    f"sqlite:///{settings.DB_PATH}", connect_args={"check_same_thread": False}
)

Base.metadata.create_all(engine)

# Columns added after the first release. create_all only creates missing
# tables, so add missing columns by hand (SQLite supports ADD COLUMN).
ADDED_COLUMNS = {
    "artworks": {"classified": "BOOLEAN NOT NULL DEFAULT 1"},
}


def migrate() -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, columns in ADDED_COLUMNS.items():
            existing = {c["name"] for c in inspector.get_columns(table)}
            for name, ddl in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


migrate()

Session = sessionmaker(bind=engine)


def get_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()
