from pathlib import Path


# E:\klocprojects\kloc-ai
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Knowledge base folder
KNOWLEDGE_DIR = PROJECT_ROOT / "kloc-knowledgebase"


def load_markdown_files():
    documents = []

    for file_path in KNOWLEDGE_DIR.rglob("*.md"):
        content = file_path.read_text(
            encoding="utf-8"
        )

        relative_path = file_path.relative_to(KNOWLEDGE_DIR)

        documents.append(
            {
                "filename": file_path.name,
                "path": str(relative_path),
                "content": content,
            }
        )

    return documents


if __name__ == "__main__":
    documents = load_markdown_files()

    print(f"Found {len(documents)} markdown files\n")

    for document in documents:
        print(
            f"- {document['path']} "
            f"({len(document['content'])} characters)"
        )