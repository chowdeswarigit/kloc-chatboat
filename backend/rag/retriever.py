from sqlalchemy import text

from app.database import engine
from rag.embeddings import generate_embedding


DEFAULT_MAX_DISTANCE = 0.47
DEFAULT_CANDIDATE_K = 10


def search_similar_chunks(
    query: str,
    top_k: int = 5,
    max_distance: float = DEFAULT_MAX_DISTANCE,
    candidate_k: int = DEFAULT_CANDIDATE_K,
):
    query_embedding = generate_embedding(query)

    sql = text("""
        SELECT
            id,
            filename,
            path,
            title,
            chunk_index,
            content,
            embedding <=> CAST(:query_embedding AS vector) AS distance
        FROM chunks
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :candidate_k;
    """)

    with engine.connect() as connection:
        result = connection.execute(
            sql,
            {
                "query_embedding": str(query_embedding),
                "candidate_k": candidate_k,
            },
        )

        rows = result.fetchall()

    filtered_rows = [
        row
        for row in rows
        if row.distance <= max_distance
    ]

    return filtered_rows[:top_k]