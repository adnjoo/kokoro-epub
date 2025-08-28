from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup

def extract_chapters(epub_path):
    book = epub.read_epub(epub_path)
    chapters = []
    for item in book.items:
        if item.get_type() == ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text()
            if text.strip():
                title = soup.title.string if soup.title else f"Chapter {len(chapters)+1}"
                chapters.append((title, text.strip()))
    return chapters

if __name__ == "__main__":
    chapters = extract_chapters("public/meta.epub")
    for i, (title, text) in enumerate(chapters, 1):
        print(f"{i}. {title} ({len(text.split())} words)")
