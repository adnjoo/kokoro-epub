from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
import re

def clean_epub_preserve_html(epub_path, output_path):
    book = epub.read_epub(epub_path)

    for item in book.items:
        if item.get_type() == ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')

            # Traverse all elements and clean string content
            for element in soup.find_all():
                if element.string:
                    original = element.string

                    # Remove the garbage pattern
                    cleaned = re.sub(
                        r'file:///E\|/.*?\(\d+ of \d+\)\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [AP]M',
                        '',
                        original,
                        flags=re.DOTALL
                    )

                    # Remove lone file:/// lines
                    cleaned = re.sub(r'^file:///E\|/.*$', '', cleaned.strip(), flags=re.MULTILINE)

                    if cleaned != original:
                        element.string.replace_with(cleaned)

            item.set_content(str(soup).encode('utf-8'))

    epub.write_epub(output_path, book)

# Example usage
clean_epub_preserve_html("input.epub", "cleaned.epub")
