from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from pathlib import Path

EPUB_PATH = Path("../public/meta.epub")

def inspect_epub(epub_path):
    book = epub.read_epub(str(epub_path))

    print("=== TOC ===")
    try:
        for entry in book.toc:
            print(entry)  # Link objects, can be inspected further
    except Exception as e:
        print("TOC not available:", e)

    print("\n=== Spine (reading order) ===")
    for idx, (idref, _) in enumerate(book.spine):
        item = book.get_item_with_id(idref)
        print(f"{idx+1}. {idref} → {getattr(item, 'file_name', '(no file name)')}")

    print("\n=== Documents ===")
    for item in book.get_items_of_type(ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        text = soup.get_text().strip().replace("\n", " ")
        snippet = text[:200].replace("\r", " ")
        print(f"{getattr(item, 'file_name', '(no file name)')} → {len(text.split())} words")
        print(f"   snippet: {snippet}...")
        print("-" * 60)


if __name__ == "__main__":
    inspect_epub(EPUB_PATH)
