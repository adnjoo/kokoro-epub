# script.py

from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from kokoro import KPipeline
import soundfile as sf
import os

from timers import Timer, estimate_total  # ⏱️ Import timing tools

# --- Config ---
book_path = "input/great.epub"
output_dir = "output"
lang_code = 'a'
voice = 'af_heart'
os.makedirs(output_dir, exist_ok=True)

# Optional: Skip earlier chapters
start_chapter = 2

# --- TTS Init ---
pipeline = KPipeline(lang_code=lang_code)

# --- Load EPUB ---
book = epub.read_epub(book_path)
chapters = [item for item in book.items if item.get_type() == ITEM_DOCUMENT]

# --- Estimate total chapters to process ---
start_chapter = start_chapter if 'start_chapter' in locals() else 0
estimated_chapters = [
    chapter for i, chapter in enumerate(chapters)
    if i >= start_chapter and len(BeautifulSoup(chapter.get_content(), 'html.parser').get_text().strip()) >= 100
]
estimate_total(estimated_chapters, avg_seconds_per_chapter=15)

# --- Total Timer Start ---
total_timer = Timer()
total_timer.start()

# --- Process Chapters ---
for i, chapter in enumerate(chapters):
    if i < start_chapter:
        continue

    soup = BeautifulSoup(chapter.get_content(), 'html.parser')
    text = soup.get_text().strip()
    if len(text) < 100:
        continue

    print(f"\n🔊 Processing chapter {i}: {chapter.get_name()}")
    chapter_timer = Timer()
    chapter_timer.start()

    for j, (_, _, audio) in enumerate(pipeline(text, voice=voice, speed=1)):
        filename = f"{output_dir}/chapter_{i:02d}_{j}.wav"
        sf.write(filename, audio, 24000)

    chapter_timer.print_elapsed(f"✅ Done chapter {i}")

# --- Total Time Summary ---
total_timer.print_elapsed("✅ All chapters")
