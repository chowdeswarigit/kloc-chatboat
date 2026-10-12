
from rag.query_rewriter import rewrite_query
from rag.multi_retriever import search_with_query_variants
from rag.generator import generate_answer
from rag.confidence import calculate_retrieval_confidence
from rag.answerability import check_answerability
from rag.grounding import evaluate_grounding


FALLBACK_ANSWER = (
    "I don't have that information in the current "
    "KLOC knowledge base."
)


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


def prepare_kloc_response(
    question: str,
    history=None,
    top_k: int = 5,
):
    """
    Prepare the RAG response without generating the final answer.

    Performs query rewriting, retrieval, confidence calculation,
    answerability checking, and grounding evaluation.
    """

    # 1. Rewrite the question using conversation history.
    retrieval_query = rewrite_query(
        question=question,
        history=history,
    )

    # 2. Retrieve relevant knowledge-base chunks.
    results = search_with_query_variants(
        retrieval_query,
        top_k=top_k,
    )

    # 3. Calculate retrieval confidence.
    confidence = calculate_retrieval_confidence(results)

    # 4. Build retrieved context.
    context = build_context(results)

    # 5. Check deterministic answerability.
    answerability = check_answerability(
        query=retrieval_query,
        results=results,
    )

    # 6. Evaluate whether the context supports the question.
    grounding = evaluate_grounding(
        question=question,
        context=context,
    )

    # 7. Return everything needed by the streaming endpoint.
    return {
        "question": question,
        "retrieval_query": retrieval_query,
        "context": context,
        "confidence": confidence,
        "answerability": answerability,
        "grounding": grounding,
        "sources": [
            {
                "filename": result.filename,
                "path": result.path.replace("\\", "/"),
                "title": result.title,
                "chunk": result.chunk_index,
                "distance": result.distance,
            }
            for result in results
        ],
    }


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

    # Generate only when grounding supports the answer.
    if (
        prepared["grounding"]["supported"]
        and prepared["grounding"]["confidence"] >= 0.70
    ):
        answer = generate_answer(
            question=question,
            context=prepared["context"],
        )
    else:
        answer = FALLBACK_ANSWER

    return {
        "question": prepared["question"],
        "retrieval_query": prepared["retrieval_query"],
        "answer": answer,
        "confidence": prepared["confidence"],
        "answerability": prepared["answerability"],
        "grounding": prepared["grounding"],
        "sources": prepared["sources"],
    }
