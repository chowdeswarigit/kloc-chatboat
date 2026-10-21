from ingestion.loader import load_markdown_files


# Soft size budget for a chunk. Sections are grouped up to this size
# but a section is never cut in the middle, so a single large section
# becomes one chunk even when it exceeds the budget.
MAX_CHUNK_CHARS = 2000

# Fragments shorter than this (e.g. a lone page label) carry no answer.
MIN_CHUNK_CHARS = 50


def build_tree(sections):
    """
    Turn a flat list of heading sections into a tree using
    heading levels. The root node holds the whole document.
    """

    root = {"level": 0, "heading": "", "content": "", "children": []}
    stack = [root]

    for section in sections:
        node = {**section, "children": []}

        # Text before the first heading belongs to the root itself.
        if node["level"] == 0:
            root["content"] = "\n\n".join(
                part for part in (root["content"], node["content"]) if part
            )
            continue

        while stack[-1]["level"] >= node["level"]:
            stack.pop()

        stack[-1]["children"].append(node)
        stack.append(node)

    return root


def render(node) -> str:
    """
    Render a node and all of its descendants as Markdown text.
    """

    parts = []

    if node["heading"]:
        parts.append(f"{'#' * node['level']} {node['heading']}")

    if node["content"]:
        parts.append(node["content"])

    for child in node["children"]:
        parts.append(render(child))

    return "\n\n".join(parts)


def has_text(node) -> bool:
    return bool(node["content"]) or any(
        has_text(child) for child in node["children"]
    )


def split_node(node, breadcrumb, max_chars):
    """
    Yield (title, content) chunks for a node.

    A node that fits the budget is emitted whole. Otherwise its
    children are packed, whole, into groups that fit the budget.
    Each chunk carries its heading breadcrumb as its title so it keeps
    its context (e.g. a case study's client name).
    """

    if node["heading"]:
        breadcrumb = breadcrumb + [node["heading"]]

    text = render(node)

    if len(text) <= max_chars or not node["children"]:
        if has_text(node):
            yield " > ".join(breadcrumb), text
        return

    intro_parts = []

    if node["heading"]:
        intro_parts.append(f"{'#' * node['level']} {node['heading']}")

    if node["content"]:
        intro_parts.append(node["content"])

    intro = "\n\n".join(intro_parts)

    groups = []
    group = []
    group_size = len(intro)

    for child in node["children"]:
        child_text = render(child)

        # Oversized children are split on their own headings.
        if len(child_text) > max_chars:
            if group:
                groups.append(group)
            group, group_size = [], len(intro)

            groups.append(child)
            continue

        if group and group_size + len(child_text) > max_chars:
            groups.append(group)
            group, group_size = [], len(intro)

        group.append(child)
        group_size += len(child_text)

    if group:
        groups.append(group)

    # Keep the intro text even if every child was split separately.
    if node["content"] and not any(isinstance(item, list) for item in groups):
        yield " > ".join(breadcrumb), intro

    for item in groups:
        if isinstance(item, dict):
            yield from split_node(item, breadcrumb, max_chars)
            continue

        if not any(has_text(child) for child in item):
            continue

        sibling_headings = " | ".join(
            child["heading"] for child in item if child["heading"]
        )

        title = " > ".join(
            part for part in (" > ".join(breadcrumb), sibling_headings) if part
        )

        body = "\n\n".join(
            part for part in [intro] + [render(child) for child in item] if part
        )

        yield title, body


def create_chunks(documents, max_chars: int = MAX_CHUNK_CHARS):
    """
    Create structure-aware chunks from loaded documents.

    Chunk boundaries always fall on heading boundaries.
    """

    all_chunks = []

    for document in documents:
        tree = build_tree(document["sections"])

        # Use the document title as the root breadcrumb unless the
        # first heading already carries it.
        root_breadcrumb = []

        first_heading = next(
            (
                section["heading"]
                for section in document["sections"]
                if section["heading"]
            ),
            "",
        )

        if document["title"] and document["title"] != first_heading:
            root_breadcrumb = [document["title"]]

        seen_contents = set()
        chunk_index = 0

        for title, content in split_node(tree, root_breadcrumb, max_chars):
            # The same section can repeat within a page; keep one copy.
            if content in seen_contents or len(content) < MIN_CHUNK_CHARS:
                continue

            seen_contents.add(content)

            all_chunks.append({
                "filename": document["filename"],
                "path": document["path"],
                "title": title or document["title"],
                "chunk_index": chunk_index,
                "content": content,
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
