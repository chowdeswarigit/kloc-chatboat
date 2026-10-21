from openai import OpenAI

from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Generate alternative search queries for a knowledge-base retrieval system.

The goal is to improve semantic retrieval.

Rules:

1. Preserve the original intent.

2. ALWAYS preserve named entities from the original question exactly
   as written: company names, client names, team or division names,
   product names, platforms, and technologies.

3. Generate exactly 2 alternative queries.

4. The FIRST alternative should be a short keyword-focused query:
   the main entity followed by the main topic.

5. The SECOND alternative should rephrase the question using
   different but equivalent domain terminology.

6. Do not invent facts or add entities that are not in the question.

7. Do not answer the question.

8. Return ONLY the two alternative queries,
   one query per line.
"""


def generate_query_variants(question: str) -> list[str]:
    response = client.responses.create(
        model="gpt-5-mini",
        instructions=SYSTEM_PROMPT,
        input=f"""
Original question:

{question}

Generate 2 alternative search queries.
""",
        reasoning={"effort": "minimal"},
    )

    lines = [
        line.strip("-• ").strip()
        for line in response.output_text.splitlines()
        if line.strip()
    ]

    variants = [question]

    for line in lines:
        if line and line not in variants:
            variants.append(line)

    return variants[:3]