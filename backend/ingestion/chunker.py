import re

from ingestion.loader import load_markdown_files


# Sections that should remain independent because they usually
# contain direct answers to user questions.
STANDALONE_SECTION_KEYWORDS = {
    "features",
    "reported outcomes",
    "services",
    "capabilities",
    "contact information",
    "pricing",
    "grounding rule",
    "response style",
    "lead qualification",
    "division selection",
}


# Short sections with descriptive/metadata information can be
# combined with the next related section.
CONTEXT_SECTION_KEYWORDS = {
    "client",
    "division",
    "platform",
    "overview",
    "background",
}


def normalize_title(title: str) -> str:
    """
    Normalize a section title for keyword matching.
    """

    return re.sub(
        r"\s+",
        " ",
        title.strip().lower(),
    )


def is_standalone_section(title: str) -> bool:
    """
    Check whether a section should remain independent.
    """

    normalized = normalize_title(title)

    return any(
        keyword in normalized
        for keyword in STANDALONE_SECTION_KEYWORDS
    )


def is_context_section(title: str) -> bool:
    """
    Check whether a section can act as contextual metadata.
    """

    normalized = normalize_title(title)

    return any(
        keyword in normalized
        for keyword in CONTEXT_SECTION_KEYWORDS
    )


def get_sections(text: str):
    """
    Split Markdown into logical sections.

    Heading-only sections are ignored.

    Context sections such as Client, Division and Platform
    may be combined with the next meaningful section.
    """

    lines = text.splitlines()

    sections = []

    current_title = None
    current_content = []

    for line in lines:

        heading_match = re.match(
            r"^#{1,3}\s+(.+)$",
            line.strip(),
        )

        if heading_match:

            if current_title is not None:

                content = "\n".join(
                    current_content
                ).strip()

                if content:
                    sections.append({
                        "title": current_title,
                        "content": content,
                    })

            current_title = heading_match.group(1).strip()
            current_content = []

        else:
            current_content.append(line)

    # Save final section
    if current_title is not None:

        content = "\n".join(
            current_content
        ).strip()

        if content:
            sections.append({
                "title": current_title,
                "content": content,
            })

    return merge_context_sections(sections)


def merge_context_sections(sections):
    """
    Merge consecutive metadata/context sections with the next
    meaningful section.

    Example:

        Client
        Sleepyhead

        Division
        KLOCOM

        Platform
        Shopify Plus

        Features
        ...

    becomes:

        Client | Division | Platform | Features

        Client:
        Sleepyhead

        Division:
        KLOCOM

        Platform:
        Shopify Plus

        Features:
        ...
    """

    if not sections:
        return []

    merged = []

    pending_context = []

    for section in sections:

        title = section["title"]
        content = section["content"]

        # Context sections are collected until we reach
        # a meaningful standalone section.
        if is_context_section(title):

            pending_context.append(section)
            continue

        # We reached a meaningful section.
        if pending_context:

            combined_parts = []

            for context in pending_context:

                combined_parts.append(
                    f"{context['title']}:\n"
                    f"{context['content']}"
                )

            combined_parts.append(
                f"{title}:\n"
                f"{content}"
            )

            combined_title = " | ".join(
                [
                    item["title"]
                    for item in pending_context
                ]
                + [title]
            )

            merged.append({
                "title": combined_title,
                "content": "\n\n".join(
                    combined_parts
                ),
            })

            pending_context = []

        else:

            merged.append({
                "title": title,
                "content": content,
            })

    # Handle any context sections at the end.
    if pending_context:

        combined_parts = []

        for context in pending_context:

            combined_parts.append(
                f"{context['title']}:\n"
                f"{context['content']}"
            )

        merged.append({
            "title": " | ".join(
                item["title"]
                for item in pending_context
            ),
            "content": "\n\n".join(
                combined_parts
            ),
        })

    return merged


def chunk_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
):
    """
    Split large sections into smaller chunks.
    """

    if len(text) <= chunk_size:
        return [text]

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - chunk_overlap

    return chunks


def create_chunks(documents):
    """
    Create semantic chunks from all knowledge-base documents.
    """

    all_chunks = []

    for document in documents:

        sections = get_sections(
            document["content"]
        )

        chunk_index = 0

        for section in sections:

            chunks = chunk_text(
                section["content"]
            )

            for chunk in chunks:

                all_chunks.append({
                    "filename": document["filename"],
                    "path": document["path"],
                    "title": section["title"],
                    "chunk_index": chunk_index,
                    "content": chunk,
                })

                chunk_index += 1

    return all_chunks


if __name__ == "__main__":

    documents = load_markdown_files()

    chunks = create_chunks(documents)

    print(f"Documents: {len(documents)}")
    print(f"Chunks: {len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):

        print("\n" + "=" * 80)
        print(f"Chunk {index}")
        print(f"File: {chunk['filename']}")
        print(f"Section: {chunk['title']}")
        print("-" * 80)
        print(chunk["content"])