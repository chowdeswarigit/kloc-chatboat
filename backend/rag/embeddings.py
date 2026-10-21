from openai import OpenAI

from app.config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"


def generate_embedding(text: str):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )

    return response.data[0].embedding


def generate_embeddings(texts: list[str]):
    """Embed several texts in one request, preserving order."""

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    return [
        item.embedding
        for item in sorted(response.data, key=lambda item: item.index)
    ]


if __name__ == "__main__":
    text = "What services does KLOC Technologies provide?"

    embedding = generate_embedding(text)

    print("Embedding generated successfully")
    print("Dimensions:", len(embedding))
    print("First 10 values:", embedding[:10])
