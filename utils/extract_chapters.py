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

            # first heading or fallback to file name
            heading = soup.find(["h1", "h2", "h3"])
            if heading and heading.get_text(strip=True):
                title = heading.get_text(strip=True)
            else:
                title = item.file_name

            chapters.append((title, text))
    return chapters


if __name__ == "__main__":
    chapters = extract_chapters("../public/5200.epub")
    for i, (title, text) in enumerate(chapters, 1):
        print(f"{i}. {title} ({len(text.split())} words)")
