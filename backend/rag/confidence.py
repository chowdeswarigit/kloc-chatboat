HIGH_CONFIDENCE_SCORE = 0.70
MEDIUM_CONFIDENCE_SCORE = 0.30


def calculate_retrieval_confidence(results):
    """
    Calculate the quality of retrieval from cross-encoder scores.

    This function evaluates retrieval quality only.
    It does NOT determine whether the question is answerable.

    Answerability is handled separately by answerability.py.
    """

    if not results:
        return {
            "confidence": 0.0,
            "level": "low",
            "best_score": None,
            "relevant_results": 0,
            "strong_results": 0,
            "reason": "no_results",
        }

    scores = [
        result.rerank_score
        for result in results
    ]

    best_score = max(scores)

    relevant_results = sum(
        1
        for score in scores
        if score >= MEDIUM_CONFIDENCE_SCORE
    )

    strong_results = sum(
        1
        for score in scores
        if score >= HIGH_CONFIDENCE_SCORE
    )

    if best_score >= HIGH_CONFIDENCE_SCORE:
        level, reason = "high", "strong_retrieval_match"
    elif best_score >= MEDIUM_CONFIDENCE_SCORE:
        level, reason = "medium", "moderate_retrieval_match"
    else:
        level, reason = "low", "weak_retrieval_match"

    return {
        "confidence": best_score,
        "level": level,
        "best_score": best_score,
        "relevant_results": relevant_results,
        "strong_results": strong_results,
        "reason": reason,
    }
