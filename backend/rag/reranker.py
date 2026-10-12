import re


STOPWORDS = {
    "what",
    "does",
    "do",
    "did",
    "is",
    "are",
    "was",
    "were",
    "the",
    "a",
    "an",
    "of",
    "for",
    "to",
    "and",
    "or",
    "in",
    "on",
    "with",
    "how",
    "can",
    "could",
    "would",
    "will",
    "it",
    "they",
    "this",
    "that",
    "their",
    "its",
    "from",
    "provide",
    "support",
}


def tokenize(text: str) -> set[str]:
    words = re.findall(
        r"[a-zA-Z0-9]+",
        text.lower(),
    )

    return {
        word
        for word in words
        if word not in STOPWORDS
        and len(word) > 2
    }


def keyword_overlap(
    query_tokens: set[str],
    text: str,
) -> float:
    """
    Calculate the percentage of query terms
    that appear in the given text.
    """

    if not query_tokens:
        return 0.0

    text_tokens = tokenize(text)

    matches = query_tokens.intersection(
        text_tokens
    )

    return len(matches) / len(query_tokens)


def calculate_rerank_score(query: str, result) -> dict:

    query_tokens = tokenize(query)

    vector_score = max(
        0.0,
        1.0 - result.distance,
    )

    keyword_score = min(
        float(result.keyword_score or 0.0),
        1.0,
    )

    title_score = keyword_overlap(
        query_tokens,
        result.title or "",
    )

    content_score = keyword_overlap(
        query_tokens,
        result.content or "",
    )

    path_score = keyword_overlap(
        query_tokens,
        result.path or "",
    )

    final_score = (
        (vector_score * 0.40)
        + (keyword_score * 0.20)
        + (title_score * 0.20)
        + (content_score * 0.15)
        + (path_score * 0.05)
    )

    return {
        "score": final_score,
        "vector_score": vector_score,
        "keyword_score": keyword_score,
        "title_score": title_score,
        "content_score": content_score,
        "path_score": path_score,
    }

def rerank_results(
    query: str,
    results,
    top_k: int = 5,
):
    """
    Rerank retrieved candidates.

    SQLAlchemy Row objects are immutable, so we return
    dictionaries containing the original result and
    reranking information instead of modifying the rows.
    """

    scored_results = []

    for result in results:
        scores = calculate_rerank_score(
            query,
            result,
        )

        scored_results.append(
            {
                "result": result,
                "score": scores["score"],
                "details": scores,
            }
        )

    # Highest reranking score first
    scored_results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scored_results[:top_k]