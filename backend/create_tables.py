from sqlalchemy import text

from app.database import Base, engine
from app.models import Chunk


print("Creating database tables...")

with engine.begin() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

Base.metadata.create_all(bind=engine)

print("Tables created successfully.")