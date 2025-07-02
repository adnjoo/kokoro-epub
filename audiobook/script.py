# script.py

from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from kokoro import KPipeline
import soundfile as sf
import os

# --- Config ---
book_path = "great.epub"
output_dir = "output"
lang_code = 'a'
voice = 'af_heart'
os.makedirs(output_dir, exist_ok=True)

# --- TTS Init ---
pipeline = KPipeline(lang_code=lang_code)

# --- Load EPUB ---
book = epub.read_epub(book_path)
chapters = [item for item in book.items if item.get_type() == ITEM_DOCUMENT]

# start_chapter = 9  # <-- Change this to whatever chapter you want to start from

for i, chapter in enumerate(chapters):
    if i < start_chapter if 'start_chapter' in locals() else 0:
        continue  # Skip chapters before start_chapter

    soup = BeautifulSoup(chapter.get_content(), 'html.parser')
    text = soup.get_text().strip()
    if len(text) < 100:
        continue

    print(f"Processing chapter {i}: {chapter.get_name()}")

    for j, (_, _, audio) in enumerate(pipeline(text, voice=voice, speed=1)):
        filename = f"{output_dir}/chapter_{i:02d}_{j}.wav"
        sf.write(filename, audio, 24000)
