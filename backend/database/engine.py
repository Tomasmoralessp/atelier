from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import settings
from database.models import Base

settings.ensure_data_dirs()

engine = create_engine(
    f"sqlite:///{settings.DB_PATH}", connect_args={"check_same_thread": False}
)

# No Alembic yet: the schema has never changed, so creating missing tables on
# startup is the whole migration story for now.
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)


def get_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()
