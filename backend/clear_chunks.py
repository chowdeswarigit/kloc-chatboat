from sqlalchemy import text

from app.database import engine


with engine.begin() as connection:
    connection.execute(
        text("TRUNCATE TABLE chunks RESTART IDENTITY;")
    )

print("Chunks table cleared successfully.")