
import re
from concurrent.futures import ThreadPoolExecutor

from rag.query_rewriter import rewrite_query
from rag.query_guard import classify_query
from rag.multi_retriever import search_with_query_variants
from rag.generator import generate_answer
from rag.confidence import calculate_retrieval_confidence
from rag.answerability import check_answerability
from rag.grounding import evaluate_grounding


FALLBACK_ANSWER = (
    "I don't have that information in the current "
    "KLOC knowledge base."
)

OUT_OF_SCOPE_ANSWER = (
    "I can only help with questions about KLOC Technologies — "
    "our teams, services, work, and how to get in touch. "
    "What would you like to know about KLOC?"
)

SMALL_TALK_ANSWER = (
    "Hi! I'm KLOC AI. Ask me anything about KLOC Technologies — "
    "our services, case studies, how we work, or how to contact us."
)

MIN_GROUNDING_CONFIDENCE = 0.70

# Greetings and thanks answered instantly, without any model calls.
SMALL_TALK_PATTERN = re.compile(
    r"^(hi+|hey+|hello+|hii+|hai|yo|hola|namaste|"
    r"good (morning|afternoon|evening)|"
    r"thanks?|thank you|thank u|thx|ty|ok(ay)?|cool|bye|goodbye)"
    r"( there| kloc( ai)?)?[\s!.?,]*$",
    re.IGNORECASE,
)


def is_small_talk(question: str) -> bool:
    return bool(SMALL_TALK_PATTERN.match(question.strip()))


def build_context(results):
    context_parts = []

    for result in results:
        source_path = result.path.replace("\\", "/")

        context_parts.append(
            f"""
SOURCE: {source_path}
SECTION: {result.title}
CHUNK: {result.chunk_index}

CONTENT:
{result.content}
"""
        )

    return "\n".join(context_parts)


def get_canned_answer(prepared) -> str | None:
    """
    Return a fixed reply when the question should not be answered
    from the knowledge base, or None when an answer should be generated.
    """

    category = prepared["scope"]["category"]

    if category == "out_of_scope":
        return OUT_OF_SCOPE_ANSWER

    if category == "small_talk":
        return SMALL_TALK_ANSWER

    if not prepared["answerability"]["is_answerable"]:
        return FALLBACK_ANSWER

    grounding = prepared["grounding"]

    if (
        not grounding["supported"]
        or grounding["confidence"] < MIN_GROUNDING_CONFIDENCE
    ):
        return FALLBACK_ANSWER

    return None


def prepare_kloc_response(
    question: str,
    history=None,
    top_k: int = 5,
):
    """
    Prepare the RAG response without generating the final answer.

    Performs query rewriting, scope filtering, retrieval with
    cross-encoder reranking, confidence calculation, answerability
    checking, and grounding evaluation.
    """

    # 0. Answer plain greetings immediately.
    if is_small_talk(question):
        return {
            "question": question,
            "retrieval_query": question,
            "context": "",
            "scope": {
                "category": "small_talk",
                "reason": "Matched a greeting.",
            },
            "confidence": calculate_retrieval_confidence([]),
            "answerability": check_answerability(question, []),
            "grounding": {
                "supported": False,
                "confidence": 0.0,
                "reason": "Not evaluated.",
            },
            "sources": [],
        }

    # 1. Rewrite the question using conversation history.
    retrieval_query = rewrite_query(
        question=question,
        history=history,
    )

    prepared = {
        "question": question,
        "retrieval_query": retrieval_query,
        "context": "",
        "confidence": calculate_retrieval_confidence([]),
        "answerability": check_answerability(retrieval_query, []),
        "grounding": {
            "supported": False,
            "confidence": 0.0,
            "reason": "Not evaluated.",
        },
        "sources": [],
    }

    # 2-3. Classify the scope and retrieve/rerank chunks in parallel.
    #      Chunks below the reranker relevance threshold are dropped.
    executor = ThreadPoolExecutor(max_workers=2)

    scope_future = executor.submit(
        classify_query,
        question=question,
        retrieval_query=retrieval_query,
    )
    results_future = executor.submit(
        search_with_query_variants,
        retrieval_query,
        top_k=top_k,
    )

    # Don't wait for retrieval to finish if the question is blocked.
    executor.shutdown(wait=False)

    prepared["scope"] = scope_future.result()

    # Questions unrelated to KLOC are blocked before answering.
    if prepared["scope"]["category"] != "in_scope":
        return prepared

    results = results_future.result()

    # 4. Calculate retrieval confidence.
    prepared["confidence"] = calculate_retrieval_confidence(results)

    # 5. Check whether any chunk is relevant enough to answer from.
    prepared["answerability"] = check_answerability(
        query=retrieval_query,
        results=results,
    )

    prepared["sources"] = [
        {
            "filename": result.filename,
            "path": result.path.replace("\\", "/"),
            "title": result.title,
            "chunk": result.chunk_index,
            "distance": result.distance,
            "rerank_score": result.rerank_score,
        }
        for result in results
    ]

    if not prepared["answerability"]["is_answerable"]:
        return prepared

    # 6. Build the context from whole chunks.
    prepared["context"] = build_context(results)

    # 7. Evaluate whether the context supports the question.
    prepared["grounding"] = evaluate_grounding(
        question=question,
        context=prepared["context"],
    )

    return prepared


def ask_kloc(
    question: str,
    history=None,
    top_k: int = 5,
):
    """
    Generate a complete answer using the existing RAG pipeline.
    """

    prepared = prepare_kloc_response(
        question=question,
        history=history,
        top_k=top_k,
    )

    answer = get_canned_answer(prepared)

    if answer is None:
        answer = generate_answer(
            question=question,
            context=prepared["context"],
        )

    return {
        "question": prepared["question"],
        "retrieval_query": prepared["retrieval_query"],
        "answer": answer,
        "scope": prepared["scope"],
        "confidence": prepared["confidence"],
        "answerability": prepared["answerability"],
        "grounding": prepared["grounding"],
        "sources": prepared["sources"],
    }
