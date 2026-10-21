from app.config import RERANK_MIN_SCORE


def check_answerability(
    query: str,
    results,
    min_score: float = RERANK_MIN_SCORE,
) -> dict:
    """
    Determine whether retrieved context is relevant enough to
    attempt an answer, using the cross-encoder relevance score of
    the best (query, chunk) pair.

    Whether the context actually contains the answer is decided
    afterwards by the grounding evaluator.
    """

    if not results:
        return {
            "is_answerable": False,
            "confidence": 0.0,
            "reason": "no_relevant_context",
            "best_score": None,
        }

    best_score = max(result.rerank_score for result in results)

    if best_score >= min_score:
        return {
            "is_answerable": True,
            "confidence": best_score,
            "reason": "relevant_context_found",
            "best_score": best_score,
        }

    return {
        "is_answerable": False,
        "confidence": best_score,
        "reason": "context_does_not_support_question",
        "best_score": best_score,
    }
