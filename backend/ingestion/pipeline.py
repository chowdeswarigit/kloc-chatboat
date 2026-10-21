from sqlalchemy import text

from ingestion.loader import load_markdown_files
from ingestion.web_loader import load_website_pages
from ingestion.chunker import create_chunks

from rag.embeddings import generate_embeddings

from app.database import SessionLocal
from app.models import Chunk, init_database


EMBEDDING_BATCH_SIZE = 64


def build_embedding_text(chunk) -> str:
    return f"""
KLOC Knowledge Base

Document: {chunk["path"]}
Topic: {chunk["title"]}

Content:
{chunk["content"]}
"""


def remove_repeated_chunks(chunks):
    """
    Website pages repeat the same blocks (testimonials, CTAs, stats)
    on many pages. Keep only the first copy of identical content.
    """

    seen = set()
    unique = []

    for chunk in chunks:
        key = " ".join(chunk["content"].split())

        if key in seen:
            continue

        seen.add(key)
        unique.append(chunk)

    return unique


def ingest_documents():
    init_database()

    print("Loading Markdown knowledge base...")

    documents = load_markdown_files()

    print(f"Loaded {len(documents)} Markdown documents")

    print("Scraping website...")

    pages = load_website_pages()

    print(f"Loaded {len(pages)} website pages")

    chunks = remove_repeated_chunks(
        create_chunks(documents + pages)
    )

    print(f"Created {len(chunks)} chunks")

    db = SessionLocal()

    try:
        # Re-ingestion replaces the previous chunks.
        db.execute(text("TRUNCATE TABLE chunks RESTART IDENTITY;"))

        for start in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
            batch = chunks[start:start + EMBEDDING_BATCH_SIZE]

            print(
                f"Embedding chunks {start + 1}-{start + len(batch)}"
                f"/{len(chunks)}..."
            )

            embeddings = generate_embeddings(
                [build_embedding_text(chunk) for chunk in batch]
            )

            for chunk, embedding in zip(batch, embeddings):
                db.add(Chunk(
                    filename=chunk["filename"],
                    path=chunk["path"],
                    title=chunk["title"],
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    embedding=embedding,
                ))

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
