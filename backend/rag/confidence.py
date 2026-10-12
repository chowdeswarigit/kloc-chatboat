HIGH_CONFIDENCE_DISTANCE = 0.40
MEDIUM_CONFIDENCE_DISTANCE = 0.47


def calculate_retrieval_confidence(results):
    """
    Calculate the quality of vector retrieval.

    This function evaluates retrieval quality only.
    It does NOT determine whether the question is answerable.

    Answerability is handled separately by answerability.py.
    """

    if not results:
        return {
            "confidence": 0.0,
            "level": "low",
            "best_distance": None,
            "relevant_results": 0,
            "strong_results": 0,
            "reason": "no_results",
        }

    distances = [
        result.distance
        for result in results
    ]

    best_distance = min(distances)

    relevant_results = sum(
        1
        for distance in distances
        if distance <= MEDIUM_CONFIDENCE_DISTANCE
    )

    strong_results = sum(
        1
        for distance in distances
        if distance <= HIGH_CONFIDENCE_DISTANCE
    )

    # Strong retrieval
    if best_distance <= HIGH_CONFIDENCE_DISTANCE:
        return {
            "confidence": 1.0,
            "level": "high",
            "best_distance": best_distance,
            "relevant_results": relevant_results,
            "strong_results": strong_results,
            "reason": "strong_retrieval_match",
        }

    # Moderate retrieval
    if (
        best_distance <= MEDIUM_CONFIDENCE_DISTANCE
        and relevant_results >= 2
    ):
        return {
            "confidence": 0.7,
            "level": "medium",
            "best_distance": best_distance,
            "relevant_results": relevant_results,
            "strong_results": strong_results,
            "reason": "multiple_relevant_results",
        }

    # Weak retrieval
    return {
        "confidence": 0.0,
        "level": "low",
        "best_distance": best_distance,
        "relevant_results": relevant_results,
        "strong_results": strong_results,
        "reason": "weak_retrieval_match",
    }