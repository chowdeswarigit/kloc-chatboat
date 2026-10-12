from evaluation.test_questions import EVALUATION_DATASET
from rag.multi_retriever import search_with_query_variants


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").lower()


def evaluate_retrieval():
    total = 0
    passed = 0
    failed = 0

    print("=" * 80)
    print("KLOC AI — HYBRID RETRIEVAL EVALUATION")
    print("=" * 80)

    for test in EVALUATION_DATASET:

        # Only evaluate retrieval questions.
        # Answerability questions are handled separately.
        if test["type"] != "retrieval":
            continue

        total += 1

        question = test["question"]

        expected_paths = [
            normalize_path(path)
            for path in test["expected_paths"]
        ]

        print()
        print("-" * 80)
        print(f"QUESTION: {question}")

        # -----------------------------------------------------
        # Hybrid Search + Reranking
        # -----------------------------------------------------

        results = search_with_query_variants(
            question,
            top_k=5,
            candidate_k=15,
        )

        retrieved_paths = [
            normalize_path(result.path)
            for result in results
        ]

        # -----------------------------------------------------
        # Recall@5
        # -----------------------------------------------------

        match = any(
            expected_path in retrieved_paths
            for expected_path in expected_paths
        )

        if match:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"

        print(f"EXPECTED : {expected_paths}")
        print(f"RETRIEVED: {retrieved_paths}")
        print(f"RESULT   : {status}")

    # ---------------------------------------------------------
    # Final metrics
    # ---------------------------------------------------------

    recall = (
        (passed / total) * 100
        if total > 0
        else 0
    )

    print()
    print("=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)

    print(f"Total retrieval tests : {total}")
    print(f"Passed                : {passed}")
    print(f"Failed                : {failed}")
    print(f"Recall@5              : {recall:.2f}%")

    print("=" * 80)


if __name__ == "__main__":
    evaluate_retrieval()