from sqlalchemy import Column, Integer, Text, String, text
from pgvector.sqlalchemy import Vector

from app.database import Base, engine


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)

    path = Column(String, nullable=False)

    title = Column(String, nullable=True)

    chunk_index = Column(Integer, nullable=False)

    content = Column(Text, nullable=False)

    embedding = Column(Vector(1536))


def init_database():
    """
    Create the pgvector extension and the chunks table if they are missing.
    """

    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    except Exception as error:
        raise RuntimeError(
            "The pgvector extension is not available on this PostgreSQL "
            "server. Install pgvector (https://github.com/pgvector/pgvector) "
            "and try again."
        ) from error

    Base.metadata.create_all(bind=engine)
