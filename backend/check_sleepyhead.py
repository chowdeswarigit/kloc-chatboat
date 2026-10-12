from sqlalchemy import text

from app.database import engine


with engine.connect() as connection:
    result = connection.execute(
        text("""
            SELECT
                id,
                title,
                chunk_index,
                LEFT(content, 300) AS content
            FROM chunks
            WHERE path LIKE '%sleepyhead%'
            ORDER BY chunk_index;
        """)
    )

    rows = result.fetchall()

    print(f"Found {len(rows)} Sleepyhead chunks\n")

    for row in rows:
        print("=" * 80)
        print(f"ID: {row.id}")
        print(f"Title: {row.title}")
        print(f"Chunk: {row.chunk_index}")
        print("Content:")
        print(row.content)
        print()