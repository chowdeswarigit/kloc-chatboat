from sqlalchemy import text

from app.database import engine
from rag.embeddings import generate_embedding


DEFAULT_VECTOR_WEIGHT = 0.70
DEFAULT_KEYWORD_WEIGHT = 0.30

DEFAULT_VECTOR_CANDIDATE_K = 15
DEFAULT_KEYWORD_CANDIDATE_K = 15


def search_hybrid_chunks(
    query: str,
    candidate_k: int = 15,
    vector_weight: float = DEFAULT_VECTOR_WEIGHT,
    keyword_weight: float = DEFAULT_KEYWORD_WEIGHT,
):
    """
    Hybrid retrieval using:

    1. pgvector semantic similarity
    2. PostgreSQL full-text keyword search

    The two result sets are merged before reranking.
    """

    query_embedding = generate_embedding(query)

    sql = text("""
        WITH vector_results AS (

            SELECT
                id,
                filename,
                path,
                title,
                chunk_index,
                content,
                embedding <=> CAST(:query_embedding AS vector)
                    AS distance

            FROM chunks

            ORDER BY embedding <=> CAST(:query_embedding AS vector)

            LIMIT :vector_candidate_k
        ),

        keyword_results AS (

            SELECT
                id,
                ts_rank_cd(
                    to_tsvector(
                        'english',
                        coalesce(filename, '') || ' ' ||
                        coalesce(path, '') || ' ' ||
                        coalesce(title, '') || ' ' ||
                        coalesce(content, '')
                    ),
                    plainto_tsquery('english', :query)
                ) AS keyword_score

            FROM chunks

            WHERE to_tsvector(
                'english',
                coalesce(filename, '') || ' ' ||
                coalesce(path, '') || ' ' ||
                coalesce(title, '') || ' ' ||
                coalesce(content, '')
            )
            @@ plainto_tsquery('english', :query)

            ORDER BY keyword_score DESC

            LIMIT :keyword_candidate_k
        ),

        combined AS (

            SELECT
                v.id,
                v.filename,
                v.path,
                v.title,
                v.chunk_index,
                v.content,
                v.distance,
                COALESCE(k.keyword_score, 0.0)
                    AS keyword_score

            FROM vector_results v

            LEFT JOIN keyword_results k
                ON v.id = k.id

            UNION

            SELECT
                c.id,
                c.filename,
                c.path,
                c.title,
                c.chunk_index,
                c.content,

                c.embedding <=> CAST(:query_embedding AS vector)
                    AS distance,

                k.keyword_score

            FROM keyword_results k

            JOIN chunks c
                ON c.id = k.id

            WHERE NOT EXISTS (
                SELECT 1
                FROM vector_results v
                WHERE v.id = k.id
            )
        )

        SELECT
            *,
            (
                (
                    :vector_weight *
                    GREATEST(0.0, 1.0 - distance)
                )
                +
                (
                    :keyword_weight *
                    LEAST(keyword_score, 1.0)
                )
            ) AS hybrid_score

        FROM combined

        ORDER BY hybrid_score DESC

        LIMIT :candidate_k;
    """)

    with engine.connect() as connection:

        result = connection.execute(
            sql,
            {
                "query_embedding": str(query_embedding),
                "query": query,
                "vector_candidate_k": DEFAULT_VECTOR_CANDIDATE_K,
                "keyword_candidate_k": DEFAULT_KEYWORD_CANDIDATE_K,
                "candidate_k": candidate_k,
                "vector_weight": vector_weight,
                "keyword_weight": keyword_weight,
            },
        )

        rows = result.fetchall()

    return rows