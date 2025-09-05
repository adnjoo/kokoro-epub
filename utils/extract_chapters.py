from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup

def extract_chapters(epub_path):
    """Extract chapter titles and text content from an EPUB file."""

    book = epub.read_epub(epub_path)
    chapters = []
    for idref, _ in book.spine:
        item = book.get_item_with_id(idref)
        if item.get_type() == ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text().strip()
            if not text:
                continue

            # find all chapter headings, not just the first
            headings = soup.find_all(["h1", "h2", "h3"])
            if headings:
                for heading in headings:
                    title = heading.get_text(strip=True)
                    content_parts = []
                    for sib in heading.next_siblings:
                        if getattr(sib, "name", None) in ["h1", "h2", "h3"]:
                            break
                        if hasattr(sib, "get_text"):
                            content_parts.append(sib.get_text(" ", strip=True))
                    chapter_text = " ".join(content_parts).strip()
                    if chapter_text:
                        chapters.append((title, chapter_text))
            else:
                chapters.append((item.file_name, text))
    return chapters
