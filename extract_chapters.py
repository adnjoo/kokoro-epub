from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup

def extract_chapters(epub_path):
    book = epub.read_epub(epub_path)
    chapters = []
    for item in book.items:
        if item.get_type() == ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text().strip()
            if not text:
                continue

            heading = soup.find(["h1", "h2", "h3"])
            if heading and heading.get_text(strip=True):
                title = heading.get_text(strip=True)
            elif soup.title and soup.title.string:
                title = soup.title.string.strip()
            else:
                title = f"Section {len(chapters)+1}"

            chapters.append((title, text))
    return chapters

if __name__ == "__main__":
    chapters = extract_chapters("public/meta.epub")
    for i, (title, text) in enumerate(chapters, 1):
        print(f"{i}. {title} ({len(text.split())} words)")
