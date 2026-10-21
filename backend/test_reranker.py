from rag.query_variants import generate_query_variants
from rag.hybrid_retriever import search_hybrid_chunks
from rag.reranker import rerank_results


questions = [
    "What features were implemented for Sleepyhead?",
    "Does KLOCOM support Shopify migrations?",
    "What does KLOCERS do?",
    "What integrations does KLOCOM support?",
    "What was built for Roam?",
]


for question in questions:

    print()
    print("=" * 80)
    print(f"QUESTION: {question}")
    print("=" * 80)

    # ---------------------------------------------------------
    # 1. Query variants
    # ---------------------------------------------------------

    query_variants = generate_query_variants(question)

    print("\nQuery variants:")

    for query in query_variants:
        print(f"  - {query}")

    # ---------------------------------------------------------
    # 2. Hybrid retrieval
    # ---------------------------------------------------------

    all_results = []

    for query in query_variants:

        results = search_hybrid_chunks(
            query,
            candidate_k=15,
        )

        all_results.extend(results)

    # ---------------------------------------------------------
    # 3. Deduplicate
    # ---------------------------------------------------------

    unique_results = {}

    for result in all_results:

        if result.id not in unique_results:

            unique_results[result.id] = result

        elif (
            result.hybrid_score
            > unique_results[result.id].hybrid_score
        ):

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
    # 4. Show hybrid candidates
    # ---------------------------------------------------------

    print("\nHYBRID CANDIDATES:")

    for index, result in enumerate(
        candidates[:10],
        start=1,
    ):

        print(
            f"{index}. "
            f"{result.path} | "
            f"{result.title} | "
            f"distance={result.distance:.4f} | "
            f"keyword={result.keyword_score:.4f} | "
            f"hybrid={result.hybrid_score:.4f}"
        )

    # ---------------------------------------------------------
    # 5. Rerank
    # ---------------------------------------------------------

    reranked = rerank_results(
        question,
        candidates,
        top_k=5,
    )

    print("\nFINAL RERANKED RESULTS:")

    for index, result in enumerate(
        reranked,
        start=1,
    ):

        print(
            f"{index}. "
            f"{result.path} | "
            f"{result.title} | "
            f"distance={result.distance:.4f} | "
            f"keyword={result.keyword_score:.4f} | "
            f"hybrid={result.hybrid_score:.4f} | "
            f"rerank={result.rerank_score:.4f}"
        )