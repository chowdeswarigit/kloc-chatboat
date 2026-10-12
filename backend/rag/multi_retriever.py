from rag.query_variants import generate_query_variants
from rag.hybrid_retriever import search_hybrid_chunks
from rag.reranker import rerank_results


def search_with_query_variants(
    question: str,
    top_k: int = 5,
    candidate_k: int = 15,
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

    candidates = sorted(
        unique_results.values(),
        key=lambda result: result.hybrid_score,
        reverse=True,
    )

    print(
        f"\nCandidate chunks before reranking: "
        f"{len(candidates)}"
    )

    # ---------------------------------------------------------
    # Reranking
    # ---------------------------------------------------------

    reranked = rerank_results(
        question,
        candidates,
        top_k=top_k,
    )

    print("\nReranked results:")

    for item in reranked:

        result = item["result"]

        print(
            f"  - {result.path} | "
            f"distance={result.distance:.4f} | "
            f"keyword={result.keyword_score:.4f} | "
            f"hybrid={result.hybrid_score:.4f} | "
            f"rerank={item['score']:.4f}"
        )

    return [
        item["result"]
        for item in reranked
    ]