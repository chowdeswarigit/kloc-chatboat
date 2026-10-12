from openai import OpenAI

from app.config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


def generate_embedding(text: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        
    )

    return response.data[0].embedding


if __name__ == "__main__":
    text = "What services does KLOC Technologies provide?"

    embedding = generate_embedding(text)

    print("Embedding generated successfully")
    print("Dimensions:", len(embedding))
    print("First 10 values:", embedding[:10])