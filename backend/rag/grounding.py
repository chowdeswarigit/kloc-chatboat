import json

from openai import OpenAI

from app.config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
You are a grounding evaluator for the KLOC AI knowledge-base chatbot.

Your job is to determine whether the provided knowledge-base context
contains enough factual information to answer the user's question.

IMPORTANT RULES:

1. Evaluate ONLY the provided context.

2. Do not use outside knowledge.

3. The context does not need to contain the exact wording of the
   question. It can contain equivalent factual information.

4. Return "supported": true only when the context contains enough
   information to produce a factual answer.

5. Return "supported": false when:
   - The context is unrelated.
   - The context only discusses the company generally but not the
     requested topic.
   - The question asks for information that is absent from the context.
   - Answering would require inventing information.

6. A weak semantic similarity is NOT enough.

7. For example:

Question:
"What is KLOC's refund policy?"

Context:
"KLOC provides Shopify development and technology talent."

Result:
supported = false

Question:
"What features were implemented for Sleepyhead?"

Context:
"Features: Mattress configurators, EMI logic, trial-period logic..."

Result:
supported = true

Return ONLY valid JSON using this structure:

{
  "supported": true,
  "confidence": 0.95,
  "reason": "The context directly contains information answering the question."
}

The confidence must be between 0 and 1.
"""


def evaluate_grounding(
    question: str,
    context: str,
) -> dict:
    """
    Use an LLM to determine whether the retrieved context
    actually supports answering the user's question.
    """

    prompt = f"""
USER QUESTION:

{question}


KNOWLEDGE BASE CONTEXT:

{context}


Determine whether the context supports answering the question.
"""

    response = client.responses.create(
        model="gpt-5-mini",
        instructions=SYSTEM_PROMPT,
        input=prompt,
        reasoning={"effort": "low"},
    )

    raw_output = response.output_text.strip()

    try:
        result = json.loads(raw_output)

        return {
            "supported": bool(result.get("supported", False)),
            "confidence": float(
                result.get("confidence", 0.0)
            ),
            "reason": result.get(
                "reason",
                "No reason provided.",
            ),
        }

    except (json.JSONDecodeError, ValueError, TypeError):
        return {
            "supported": False,
            "confidence": 0.0,
            "reason": "Grounding evaluator returned invalid JSON.",
        }