from app.config import RERANK_MIN_SCORE

from rag.query_variants import generate_query_variants
from rag.hybrid_retriever import search_hybrid_chunks
from rag.reranker import rerank_results


def search_with_query_variants(
    question: str,
    top_k: int = 5,
    candidate_k: int = 40,
    min_score: float = RERANK_MIN_SCORE,
):
    query_variants = generate_query_variants(question)

    print("\nQuery variants:")

    for query in query_variants:
        print(f"  - {query}")

    all_results = []

    for query in query_variants:

        results = search_hybrid_chunks(
            query,
            candidate_k=candidate_k,
        )

        all_results.extend(results)

    # ---------------------------------------------------------
    # Remove duplicate chunks
    # ---------------------------------------------------------

    unique_results = {}

    for result in all_results:

        if result.id not in unique_results:

            unique_results[result.id] = result

        else:

            existing = unique_results[result.id]

            if result.hybrid_score > existing.hybrid_score:

                unique_results[result.id] = result

    candidates = list(unique_results.values())

    print(
        f"\nCandidate chunks before reranking: "
        f"{len(candidates)}"
    )

    # ---------------------------------------------------------
    # Cross-encoder reranking
    # ---------------------------------------------------------

    reranked = rerank_results(
        question,
        candidates,
        top_k=top_k,
        min_score=min_score,
    )

    print("\nReranked results:")

    for chunk in reranked:

        print(
            f"  - {chunk.path} | "
            f"distance={chunk.distance:.4f} | "
            f"hybrid={chunk.hybrid_score:.4f} | "
            f"rerank={chunk.rerank_score:.4f}"
        )

    return reranked
