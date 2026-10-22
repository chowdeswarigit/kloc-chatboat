# from dataclasses import dataclass
# from functools import lru_cache

# import torch
# from sentence_transformers import CrossEncoder

# from app.config import RERANKER_MODEL


# @dataclass
# class RetrievedChunk:
#     id: int
#     filename: str
#     path: str
#     title: str
#     chunk_index: int
#     content: str
#     distance: float
#     keyword_score: float
#     hybrid_score: float
#     rerank_score: float


# @lru_cache(maxsize=1)
# def get_reranker() -> CrossEncoder:
#     """Load the cross-encoder once per process."""

#     return CrossEncoder(RERANKER_MODEL)


# def build_passage(result) -> str:
#     return f"{result.title or ''}\n\n{result.content}".strip()


# def score_pairs(query: str, passages: list[str]) -> list[float]:
#     """
#     Score (query, passage) pairs with the cross-encoder.

#     Scores are relevance probabilities between 0 and 1.
#     """

#     if not passages:
#         return []

#     scores = get_reranker().predict(
#         [(query, passage) for passage in passages],
#         batch_size=16,
#         show_progress_bar=False,
#         # Some cross-encoders return raw logits; normalise all of
#         # them to 0-1 so RERANK_MIN_SCORE means the same thing.
#         activation_fn=torch.nn.Sigmoid(),
#     )

#     return [float(score) for score in scores]


# def rerank_results(
#     query: str,
#     results,
#     top_k: int = 5,
#     min_score: float = 0.0,
# ):
#     """
#     Rerank retrieved candidates with the cross-encoder.

#     Returns RetrievedChunk objects ordered by relevance, keeping only
#     those scoring at least `min_score`. Chunk content is returned whole.
#     """

#     scores = score_pairs(
#         query,
#         [build_passage(result) for result in results],
#     )

#     reranked = [
#         RetrievedChunk(
#             id=result.id,
#             filename=result.filename,
#             path=result.path,
#             title=result.title,
#             chunk_index=result.chunk_index,
#             content=result.content,
#             distance=float(result.distance),
#             keyword_score=float(result.keyword_score or 0.0),
#             hybrid_score=float(result.hybrid_score),
#             rerank_score=score,
#         )
#         for result, score in zip(results, scores)
#         if score >= min_score
#     ]

#     reranked.sort(
#         key=lambda chunk: chunk.rerank_score,
#         reverse=True,
#     )

#     return reranked[:top_k]

from dataclasses import dataclass
from functools import lru_cache

import torch
from sentence_transformers import CrossEncoder

from app.config import RERANKER_MODEL


@dataclass
class RetrievedChunk:
    id: int
    filename: str
    path: str
    title: str
    chunk_index: int
    content: str
    distance: float
    keyword_score: float
    hybrid_score: float
    rerank_score: float


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    """Load the cross-encoder once per process on CPU."""

    torch.set_num_threads(1)

    return CrossEncoder(
        RERANKER_MODEL,
        device="cpu",
    )


def build_passage(result) -> str:
    return f"{result.title or ''}\n\n{result.content}".strip()


def score_pairs(query: str, passages: list[str]) -> list[float]:
    """Score query-passage pairs and normalize scores to 0-1."""

    if not passages:
        return []

    scores = get_reranker().predict(
        [(query, passage) for passage in passages],
        batch_size=1,
        show_progress_bar=False,
        activation_fn=torch.nn.Sigmoid(),
    )

    return [float(score) for score in scores]


def rerank_results(
    query: str,
    results,
    top_k: int = 5,
    min_score: float = 0.0,
):
    """Rerank retrieved candidates and return the top relevant chunks."""

    scores = score_pairs(
        query,
        [build_passage(result) for result in results],
    )

    reranked = [
        RetrievedChunk(
            id=result.id,
            filename=result.filename,
            path=result.path,
            title=result.title,
            chunk_index=result.chunk_index,
            content=result.content,
            distance=float(result.distance),
            keyword_score=float(result.keyword_score or 0.0),
            hybrid_score=float(result.hybrid_score),
            rerank_score=score,
        )
        for result, score in zip(results, scores)
        if score >= min_score
    ]

    reranked.sort(
        key=lambda chunk: chunk.rerank_score,
        reverse=True,
    )

    return reranked[:top_k]
