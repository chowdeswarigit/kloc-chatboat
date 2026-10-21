from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from app.config import WEBSITE_URL, WEBSITE_MAX_PAGES


REQUEST_TIMEOUT = 20

HEADERS = {
    "User-Agent": "KLOC-AI-Ingestion/1.0 (+https://kloctech.com)",
}

# Elements that never carry readable page content.
NON_CONTENT_TAGS = [
    "script",
    "style",
    "noscript",
    "template",
    "svg",
    "iframe",
    "form",
    "button",
    "nav",
]

# Site chrome that repeats on every page. Only removed outside <main>,
# because pages also use <header>/<footer> inside content sections.
SITE_CHROME_TAGS = ["header", "footer", "aside"]

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

# Elements whose text is collected as one paragraph-like block.
BLOCK_TAGS = {
    "p",
    "li",
    "blockquote",
    "dt",
    "dd",
    "td",
    "th",
    "figcaption",
    "pre",
}


def fetch(url: str) -> requests.Response | None:
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response

    except requests.RequestException as error:
        print(f"  ! Failed to fetch {url}: {error}")
        return None


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"

    return f"{parsed.scheme}://{parsed.netloc}{path}"


def is_same_site(url: str, base_url: str) -> bool:
    return urlparse(url).netloc == urlparse(base_url).netloc


def get_sitemap_urls(base_url: str) -> list[str]:
    """
    Read page URLs from sitemap.xml, following nested sitemap indexes.
    """

    pending = [urljoin(base_url, "/sitemap.xml")]
    seen_sitemaps = set()
    urls = []

    while pending:
        sitemap_url = pending.pop()

        if sitemap_url in seen_sitemaps:
            continue

        seen_sitemaps.add(sitemap_url)

        response = fetch(sitemap_url)

        if response is None:
            continue

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError:
            continue

        for element in root.iter():
            if not element.tag.endswith("loc") or not element.text:
                continue

            loc = element.text.strip()

            if loc.endswith(".xml"):
                pending.append(loc)
            else:
                urls.append(loc)

    return urls


def get_page_links(soup: BeautifulSoup, page_url: str) -> list[str]:
    links = []

    for anchor in soup.find_all("a", href=True):
        url = urljoin(page_url, anchor["href"])
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            continue

        links.append(url)

    return links


def clean_text(text: str) -> str:
    return " ".join(text.split())


def extract_sections(soup: BeautifulSoup) -> list[dict]:
    """
    Walk the main content in document order and group text under
    the nearest preceding heading.

    Returns sections in the same shape as the Markdown loader:
    [{"level": int, "heading": str, "content": str}, ...]
    """

    for tag in soup.find_all(NON_CONTENT_TAGS):
        tag.decompose()

    main = soup.find("main")

    for tag in soup.find_all(SITE_CHROME_TAGS):
        if main is None or main not in tag.parents:
            tag.decompose()

    root = main or soup.body or soup

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

    for element in root.find_all(HEADING_TAGS | BLOCK_TAGS):

        # Skip blocks nested inside another collected block
        # (e.g. <p> inside <li>) so text is not duplicated.
        if element.find_parent(BLOCK_TAGS) is not None:
            continue

        text = clean_text(element.get_text(" ", strip=True))

        if not text:
            continue

        if element.name in HEADING_TAGS:
            flush()
            current = {
                "level": int(element.name[1]),
                "heading": text,
                "lines": [],
            }

        elif element.name == "li":
            current["lines"].append(f"- {text}")

        else:
            current["lines"].append(text)

    flush()

    return sections


def wrap_loose_text(soup_root) -> None:
    """
    Wrap direct text in leaf <div>/<span> elements in <p> tags so
    extract_sections() picks up content that is not inside a
    semantic block element (common on marketing sites for stats,
    taglines and card bodies).
    """

    for element in soup_root.find_all(["div", "span"]):
        if element.find(HEADING_TAGS | BLOCK_TAGS | {"div"}):
            continue

        if element.find_parent(HEADING_TAGS | BLOCK_TAGS) is not None:
            continue

        text = clean_text(element.get_text(" ", strip=True))

        if text:
            element.name = "p"


def parse_page(html: bytes, url: str) -> tuple[dict, BeautifulSoup]:
    # Links are read from the untouched tree because content
    # extraction removes navigation and footer elements.
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("title")
    title = clean_text(title_tag.get_text()) if title_tag else url

    content_soup = BeautifulSoup(html, "lxml")
    wrap_loose_text(content_soup)

    sections = extract_sections(content_soup)

    path = urlparse(url).path.strip("/") or "home"

    document = {
        "filename": path.split("/")[-1],
        "path": url,
        "title": title,
        "sections": sections,
    }

    return document, soup


def load_website_pages(
    base_url: str = WEBSITE_URL,
    max_pages: int = WEBSITE_MAX_PAGES,
) -> list[dict]:
    """
    Crawl the website, starting from its sitemap and following
    same-site links, and extract page content with BeautifulSoup.
    """

    queue = [base_url] + get_sitemap_urls(base_url)
    visited = set()
    documents = []

    while queue and len(visited) < max_pages:
        url = normalize_url(queue.pop(0))

        if url in visited or not is_same_site(url, base_url):
            continue

        visited.add(url)

        response = fetch(url)

        if response is None:
            continue

        if "text/html" not in response.headers.get("content-type", ""):
            continue

        print(f"  Scraped {url}")

        # Raw bytes let BeautifulSoup use the charset the page declares.
        document, soup = parse_page(response.content, url)

        if any(section["content"] for section in document["sections"]):
            documents.append(document)

        for link in get_page_links(soup, url):
            if normalize_url(link) not in visited:
                queue.append(link)

    return documents


if __name__ == "__main__":
    pages = load_website_pages()

    print(f"\nScraped {len(pages)} pages\n")

    for page in pages:
        characters = sum(
            len(section["content"])
            for section in page["sections"]
        )

        print(
            f"- {page['path']} "
            f"({len(page['sections'])} sections, {characters} characters)"
        )
