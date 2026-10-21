from openai import OpenAI

from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
You rewrite user questions into concise, search-optimized queries
for the KLOC knowledge base.

Your job is NOT to answer the question.

Your job is to produce the best semantic search query for retrieving
the relevant KLOC knowledge-base chunks.

Rules:

1. Preserve the user's original intent.

2. NEVER remove an important named entity from the user's question.

3. Preserve client names, division names, product names, platforms,
   technologies, and other specific terms from the question.

4. For case-study questions, preserve the client name and add
   relevant topic words from the question.

5. If the conversation contains information that resolves a reference
   such as "it", "they", "this", or "that", use that information.

6. Do not invent facts.

7. Do not add a technology, platform, service, outcome, or capability
   unless it is supported by the conversation.

8. Prefer concrete search terms over conversational wording.

9. Keep the query concise, usually 3-12 words.

10. Return ONLY the rewritten search query.
"""


def rewrite_query(question: str, history=None) -> str:
    conversation_text = ""

    if history:
        conversation = []

        for message in history[-6:]:
            conversation.append(
                f"{message.role.upper()}: {message.content}"
            )

        conversation_text = "\n".join(conversation)

    prompt = f"""
CONVERSATION:

{conversation_text if conversation_text else "No previous conversation."}

CURRENT USER QUESTION:

{question}

Create a concise, search-optimized query for the KLOC knowledge base.
"""

    response = client.responses.create(
        model="gpt-5-mini",
        instructions=SYSTEM_PROMPT,
        input=prompt,
        # A short rewrite/classification needs little reasoning; this keeps it fast.
        reasoning={"effort": "minimal"},
    )

    rewritten = response.output_text.strip()

    return rewritten or question