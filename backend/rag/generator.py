
from openai import OpenAI

from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
You are KLOC AI, an intelligent business and technology assistant
for KLOC Technologies.

Answer questions using ONLY the provided KLOC knowledge base context.

Rules:
1. Do not invent information.
2. Do not make up pricing, timelines, clients, technologies,
   partnerships, certifications, or guarantees.
3. If the answer is not available in the provided context,
   say:
   "I don't have that information in the current KLOC knowledge base."
4. Be clear, professional, and concise.
5. When useful, mention the relevant KLOC team or service named
   in the context.
"""


def build_prompt(question: str, context: str) -> str:
    return f"""
KLOC KNOWLEDGE BASE CONTEXT:

{context}

USER QUESTION:

{question}

Answer the user's question using only the context above.
"""


def generate_answer(question: str, context: str) -> str:
    """Generate a complete answer in one response."""

    response = client.responses.create(
        model="gpt-5-mini",
        instructions=SYSTEM_PROMPT,
        input=build_prompt(question, context),
    )

    return response.output_text


def stream_answer(question: str, context: str):
    """Yield answer text fragments as they arrive from OpenAI."""

    stream = client.responses.create(
        model="gpt-5-mini",
        instructions=SYSTEM_PROMPT,
        input=build_prompt(question, context),
        stream=True,
    )

    for event in stream:
        if event.type == "response.output_text.delta":
            yield event.delta
