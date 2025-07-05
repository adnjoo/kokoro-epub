"""
processor.py

Audio generation from EPUB and TXT files using Kokoro TTS pipeline.
"""

from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from kokoro import KPipeline
import soundfile as sf
import os
from timers import Timer, estimate_total  # ⏱️ Import timing tools
import re

def process_epub(
    book_path,
    output_dir="output",
    lang_code='a',
    voice='af_heart',
    start_chapter=0,
    progress_callback=None,
    chapter_callback=None
):
    """
    Convert an EPUB file to audio files (WAV) using Kokoro TTS.
    Each sufficiently long chapter becomes one or more audio files.
    """
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

def process_txt(
    txt_path,
    output_dir="output",
    lang_code='a',
    voice='af_heart',
    progress_callback=None,
    chunk_callback=None
):
    """
    Convert a TXT file to audio files (WAV) using Kokoro TTS.
    Each sufficiently long paragraph (split by blank lines) becomes one or more audio files.
    """
    os.makedirs(output_dir, exist_ok=True)
    pipeline = KPipeline(lang_code=lang_code)
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Replace single newlines (not part of double newline) with a space
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    # Only include paragraphs with at least 100 characters; this will skip short quotes or poetry
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if len(p.strip()) >= 100]
    estimate_total(paragraphs, avg_seconds_per_chapter=15)

    total_timer = Timer()
    total_timer.start()

    for i, paragraph in enumerate(paragraphs):
        if progress_callback:
            progress_callback(f"🔊 Processing chunk {i}")
        chunk_timer = Timer()
        chunk_timer.start()
        for j, (_, _, audio) in enumerate(pipeline(paragraph, voice=voice, speed=1)):
            filename = f"{output_dir}/chunk_{i:02d}_{j}.wav"
            sf.write(filename, audio, 24000)
            if chunk_callback:
                chunk_callback(filename)
        chunk_timer.print_elapsed(f"✅ Done chunk {i}")
    total_timer.print_elapsed("✅ All chunks")
    if progress_callback:
        progress_callback("✅ All chunks done!")

if __name__ == "__main__":
    # CLI usage for backward compatibility (EPUB only)
    process_epub(
        book_path="input/gift.epub",
        output_dir="output",
        lang_code='a',
        voice='af_heart'
    )

