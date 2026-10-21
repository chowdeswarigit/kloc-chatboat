from pathlib import Path
import re


# E:\klocprojects\kloc-ai
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Knowledge base folder
KNOWLEDGE_DIR = PROJECT_ROOT / "kloc-knowledgebase"


def parse_markdown_sections(text: str) -> list[dict]:
    """
    Split Markdown into heading sections:
    [{"level": int, "heading": str, "content": str}, ...]

    Text before the first heading is returned with level 0.
    """

    sections = []
    current = {"level": 0, "heading": "", "lines": []}

    def flush():
        content = "\n".join(current["lines"]).strip()

        if current["heading"] or content:
            sections.append({
                "level": current["level"],
                "heading": current["heading"],
                "content": content,
            })

    for line in text.splitlines():
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())

        if heading_match:
            flush()
            current = {
                "level": len(heading_match.group(1)),
                "heading": heading_match.group(2).strip(),
                "lines": [],
            }
        else:
            current["lines"].append(line)

    flush()

    return sections


def load_markdown_files():
    documents = []

    for file_path in KNOWLEDGE_DIR.rglob("*.md"):
        content = file_path.read_text(
            encoding="utf-8"
        )

        relative_path = file_path.relative_to(KNOWLEDGE_DIR)

        sections = parse_markdown_sections(content)

        title = next(
            (section["heading"] for section in sections if section["heading"]),
            file_path.stem,
        )

        documents.append(
            {
                "filename": file_path.name,
                "path": str(relative_path).replace("\\", "/"),
                "title": title,
                "sections": sections,
            }
        )

    return documents


if __name__ == "__main__":
    documents = load_markdown_files()

    print(f"Found {len(documents)} markdown files\n")

    for document in documents:
        print(
            f"- {document['path']} "
            f"({len(document['sections'])} sections)"
        )
