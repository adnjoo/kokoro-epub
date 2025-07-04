# script.py

from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from kokoro import KPipeline
import soundfile as sf
import os
from timers import Timer, estimate_total  # ⏱️ Import timing tools

def process_epub(
    book_path,
    output_dir="output",
    lang_code='a',
    voice='af_heart',
    start_chapter=0,
    progress_callback=None,
    chapter_callback=None
):
    os.makedirs(output_dir, exist_ok=True)
    pipeline = KPipeline(lang_code=lang_code)
    book = epub.read_epub(book_path)
    chapters = [item for item in book.items if item.get_type() == ITEM_DOCUMENT]

    estimated_chapters = [
        chapter for i, chapter in enumerate(chapters)
        if i >= start_chapter and len(BeautifulSoup(chapter.get_content(), 'html.parser').get_text().strip()) >= 100
    ]
    estimate_total(estimated_chapters, avg_seconds_per_chapter=15)

    total_timer = Timer()
    total_timer.start()

    for i, chapter in enumerate(chapters):
        if i < start_chapter:
            continue
        soup = BeautifulSoup(chapter.get_content(), 'html.parser')
        text = soup.get_text().strip()
        if len(text) < 100:
            continue
        chapter_name = chapter.get_name()
        if progress_callback:
            progress_callback(f"🔊 Processing chapter {i}: {chapter_name}")
        chapter_timer = Timer()
        chapter_timer.start()
        for j, (_, _, audio) in enumerate(pipeline(text, voice=voice, speed=1)):
            filename = f"{output_dir}/chapter_{i:02d}_{j}.wav"
            sf.write(filename, audio, 24000)
            if chapter_callback:
                chapter_callback(filename)
        chapter_timer.print_elapsed(f"✅ Done chapter {i}")
    total_timer.print_elapsed("✅ All chapters")
    if progress_callback:
        progress_callback("✅ All chapters done!")

if __name__ == "__main__":
    # CLI usage for backward compatibility
    process_epub(
        book_path="input/great.epub",
        output_dir="output",
        lang_code='a',
        voice='af_heart'
    )
