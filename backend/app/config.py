import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Website ingested alongside the Markdown knowledge base.
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://kloctech.com/")
WEBSITE_MAX_PAGES = int(os.getenv("WEBSITE_MAX_PAGES", "100"))

# Cross-encoder used to rerank retrieved chunks.
RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL",
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
)

# Chunks scoring below this reranker relevance (0-1) are discarded.
# If none remain, the question is treated as unrelated to the knowledge base.
RERANK_MIN_SCORE = float(os.getenv("RERANK_MIN_SCORE", "0.10"))
