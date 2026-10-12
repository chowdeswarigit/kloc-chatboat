from sqlalchemy import Column, Integer, Text, String
from pgvector.sqlalchemy import Vector

from app.database import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)

    path = Column(String, nullable=False)

    title = Column(String, nullable=True)

    chunk_index = Column(Integer, nullable=False)

    content = Column(Text, nullable=False)

    embedding = Column(Vector(1536))