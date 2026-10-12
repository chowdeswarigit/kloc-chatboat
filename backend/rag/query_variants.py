from openai import OpenAI

from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Generate alternative search queries for a knowledge-base retrieval system.

The goal is to improve semantic retrieval.

Rules:

1. Preserve the original intent.

2. ALWAYS preserve important named entities such as:
   - Sleepyhead
   - Pothys
   - Curio
   - Roam
   - Sari Connected
   - KLOCOM
   - KLOCAPPS
   - KLOCERS

3. Generate exactly 2 alternative queries.

4. The FIRST alternative should be a short keyword-focused query.

   Format:
   [important entity] + [main topic]

   Example:
   Sleepyhead features
   Sleepyhead reported outcomes
   KLOCOM Shopify migrations
   KLOCERS delivery pods

5. The SECOND alternative should add useful domain-specific
   terminology from the original question.

   Example:
   Sleepyhead Shopify Plus features
   Sleepyhead conversion rate page load downtime
   KLOCOM Shopify migration services

6. For case studies, ALWAYS preserve the client name.

7. For questions about features, include:
   features

8. For questions about outcomes, include:
   reported outcomes
   or specific outcome terms mentioned in the question.

9. Do not invent facts.

10. Do not answer the question.

11. Return ONLY the two alternative queries,
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