
from typing import List, Literal
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from rag.rag_pipeline import prepare_kloc_response, get_canned_answer
from rag.generator import stream_answer


router = APIRouter(
    prefix="/api",
    tags=["chat"],
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str
    history: List[ChatMessage] = Field(default_factory=list)


def format_event(event_type: str, data: dict) -> str:
    return (
        f"event: {event_type}\n"
        f"data: {json.dumps(data)}\n\n"
    )


@router.post("/chat")
def chat(request: ChatRequest):
    # Run scope filtering, retrieval, reranking, and grounding first.
    prepared = prepare_kloc_response(
        question=request.question,
        history=request.history,
    )

    def generate_events():
        # Send metadata before the answer text.
        metadata = {
            "question": prepared["question"],
            "retrieval_query": prepared["retrieval_query"],
            "scope": prepared["scope"],
            "confidence": prepared["confidence"],
            "answerability": prepared["answerability"],
            "grounding": prepared["grounding"],
            "sources": prepared["sources"],
        }

        yield format_event("metadata", metadata)

        try:
            canned_answer = get_canned_answer(prepared)

            if canned_answer is None:
                for delta in stream_answer(
                    question=request.question,
                    context=prepared["context"],
                ):
                    yield format_event("token", {"text": delta})
            else:
                yield format_event("token", {"text": canned_answer})

            yield format_event("done", {"status": "completed"})

        except Exception:
            yield format_event(
                "error",
                {"message": "The response stream was interrupted."},
            )

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
