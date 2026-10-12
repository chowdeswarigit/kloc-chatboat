import re


# Words that usually don't carry useful meaning for retrieval validation.
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


# Important question-intent terms for the KLOC knowledge base.
INTENT_KEYWORDS = {
    "features",
    "feature",
    "implemented",
    "implementation",

    "outcome",
    "outcomes",
    "result",
    "results",
    "impact",

    "pricing",
    "price",
    "cost",
    "costs",
    "fee",
    "fees",

    "refund",
    "refunds",
    "policy",

    "migration",
    "migrations",
    "migrate",

    "integration",
    "integrations",

    "capability",
    "capabilities",
    "services",
    "service",

    "dedicated",
    "teams",
    "team",
    "engineers",
    "engineering",

    "contact",
    "email",
    "phone",
    "location",
    "located",
    "address",
}


def tokenize(text: str) -> set[str]:
    """
    Convert text into normalized keywords.
    """

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


def extract_intent_keywords(text: str) -> set[str]:
    """
    Extract question-intent keywords.
    """

    tokens = tokenize(text)

    return tokens.intersection(INTENT_KEYWORDS)


def get_result_text(result) -> str:
    """
    Combine metadata and content from a retrieved chunk.
    """

    return " ".join(
        [
            result.path or "",
            result.title or "",
            result.content or "",
        ]
    ).lower()


def calculate_keyword_overlap(
    query: str,
    result,
) -> dict:
    """
    Calculate how strongly the query's important terms
    appear in the retrieved result.
    """

    query_tokens = tokenize(query)

    result_tokens = tokenize(
        get_result_text(result)
    )

    if not query_tokens:
        return {
            "matched_terms": [],
            "coverage": 0.0,
        }

    matched_terms = sorted(
        query_tokens.intersection(result_tokens)
    )

    coverage = (
        len(matched_terms)
        / len(query_tokens)
    )

    return {
        "matched_terms": matched_terms,
        "coverage": coverage,
    }


def check_answerability(
    query: str,
    results,
) -> dict:
    """
    Determine whether retrieved context contains
    enough evidence to answer the user's question.
    """

    if not results:
        return {
            "is_answerable": False,
            "confidence": 0.0,
            "reason": "no_retrieved_context",
            "matched_intent_keywords": [],
            "intent_coverage": 0.0,
        }

    best_result = min(
        results,
        key=lambda result: result.distance,
    )

    # ---------------------------------------------------------
    # 1. Extract question intent
    # ---------------------------------------------------------

    intent_keywords = extract_intent_keywords(query)

    result_text = get_result_text(best_result)
    result_tokens = tokenize(result_text)

    matched_intent_keywords = sorted(
        intent_keywords.intersection(result_tokens)
    )

    if intent_keywords:
        intent_coverage = (
            len(matched_intent_keywords)
            / len(intent_keywords)
        )
    else:
        intent_coverage = 0.0

    # ---------------------------------------------------------
    # 2. Calculate normal keyword overlap
    # ---------------------------------------------------------

    keyword_result = calculate_keyword_overlap(
        query,
        best_result,
    )

    keyword_coverage = keyword_result["coverage"]

    # ---------------------------------------------------------
    # 3. Strong answerability
    # ---------------------------------------------------------

    if (
        best_result.distance <= 0.40
        and (
            intent_coverage >= 0.5
            or keyword_coverage >= 0.5
        )
    ):
        return {
            "is_answerable": True,
            "confidence": 1.0,
            "reason": "strong_context_support",
            "best_distance": best_result.distance,
            "matched_intent_keywords": matched_intent_keywords,
            "intent_coverage": intent_coverage,
            "matched_keywords": keyword_result["matched_terms"],
            "keyword_coverage": keyword_coverage,
        }

    # ---------------------------------------------------------
    # 4. Medium answerability
    # ---------------------------------------------------------

    if (
        best_result.distance <= 0.47
        and intent_coverage >= 0.5
    ):
        return {
            "is_answerable": True,
            "confidence": 0.7,
            "reason": "moderate_context_support",
            "best_distance": best_result.distance,
            "matched_intent_keywords": matched_intent_keywords,
            "intent_coverage": intent_coverage,
            "matched_keywords": keyword_result["matched_terms"],
            "keyword_coverage": keyword_coverage,
        }

    # ---------------------------------------------------------
    # 5. Weak / unsupported context
    # ---------------------------------------------------------

    return {
        "is_answerable": False,
        "confidence": 0.0,
        "reason": "context_does_not_support_question",
        "best_distance": best_result.distance,
        "matched_intent_keywords": matched_intent_keywords,
        "intent_coverage": intent_coverage,
        "matched_keywords": keyword_result["matched_terms"],
        "keyword_coverage": keyword_coverage,
    }