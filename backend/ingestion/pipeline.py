from ingestion.loader import load_markdown_files
from ingestion.chunker import create_chunks

from rag.embeddings import generate_embedding

from app.database import SessionLocal
from app.models import Chunk


def ingest_documents():
    print("Loading documents...")

    documents = load_markdown_files()

    print(f"Loaded {len(documents)} documents")

    chunks = create_chunks(documents)

    print(f"Created {len(chunks)} chunks")

    db = SessionLocal()

    try:
        for index, chunk in enumerate(chunks, start=1):

            print(
                f"Embedding chunk {index}/{len(chunks)}..."
            )

            embedding_text = f"""
KLOC Knowledge Base

Document: {chunk["path"]}
Topic: {chunk["title"]}

Content:
{chunk["content"]}
"""

            embedding = generate_embedding(
                embedding_text
            )

            db_chunk = Chunk(
                filename=chunk["filename"],
                path=chunk["path"],
                title=chunk["title"],
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                embedding=embedding,
            )

            db.add(db_chunk)

        db.commit()

        print()
        print("Ingestion completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    ingest_documents()