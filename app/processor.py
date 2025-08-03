"""
processor.py

Audio generation from EPUB and TXT files using Kokoro TTS pipeline.
"""

from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from kokoro import KPipeline
import soundfile as sf
import os
from utils.timers import Timer, estimate_total  # ⏱️ Import timing tools
import re
from PyPDF2 import PdfReader

# TODO: begin code block - try without this
import os
import sys

if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    bundle_dir = sys._MEIPASS
    os.environ['HF_HOME'] = bundle_dir
    os.environ['HUGGINGFACE_HUB_CACHE'] = bundle_dir
# TODO: end code block

MIN_TEXT_LENGTH = 100

def process_epub(
    book_path,
    output_dir="output",
    lang_code='a',
    voice='af_heart',
    start_chapter=0,
    progress_callback=None,
    chapter_callback=None,
    enforce_min_length=True,
    device=None,
    progress_update=None
):
    """
    Convert an EPUB file to audio files (WAV) using Kokoro TTS.
    Each sufficiently long chapter becomes one or more audio files.
    """
    print(f"process_epub called with: {book_path}, output_dir={output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    if device is None:
        # Auto-detect
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        pipeline = KPipeline(lang_code=lang_code, device=device)
    except Exception as e:
        print(f"Error initializing KPipeline: {e}")
        return
    book = epub.read_epub(book_path)
    chapters = [item for item in book.items if item.get_type() == ITEM_DOCUMENT]
    print(f"Found {len(chapters)} chapters in EPUB")

    if enforce_min_length:
        valid_chapters = [
            chapter for i, chapter in enumerate(chapters)
            if i >= start_chapter and len(BeautifulSoup(chapter.get_content(), 'html.parser').get_text().strip()) >= MIN_TEXT_LENGTH
        ]
    else:
        valid_chapters = [chapter for i, chapter in enumerate(chapters) if i >= start_chapter]
    estimate_total(valid_chapters, avg_seconds_per_chapter=15)

    total_timer = Timer()
    total_timer.start()

    valid_idx = 0
    for i, chapter in enumerate(chapters):
        if i < start_chapter:
            continue
        soup = BeautifulSoup(chapter.get_content(), 'html.parser')
        text = soup.get_text().strip()
        if enforce_min_length and len(text) < MIN_TEXT_LENGTH:
            continue
        chapter_name = chapter.get_name()
        if progress_callback:
            progress_callback(f"🔊 Processing chapter {i}: {chapter_name}")
        chapter_timer = Timer()
        chapter_timer.start()
        for j, (_, _, audio) in enumerate(pipeline(text, voice=voice, speed=1, split_pattern=r'\n{2,}')):
            filename = f"{output_dir}/chapter_{i:02d}_{j}.wav"
            sf.write(filename, audio, 24000)
            if chapter_callback:
                chapter_callback(filename)
        chapter_timer.print_elapsed(f"✅ Done chapter {i}")
        if progress_update:
            progress_update(valid_idx + 1)  # 1-based
        valid_idx += 1
    total_timer.print_elapsed("✅ All chapters")
    if progress_callback:
        progress_callback("✅ All chapters done!")

def process_txt(
    txt_path,
    output_dir="output",
    lang_code='a',
    voice='af_heart',
    progress_callback=None,
    chunk_callback=None,
    enforce_min_length=True,
    device=None,
    progress_update=None
):
    """
    Convert a TXT file to audio files (WAV) using Kokoro TTS.
    Each sufficiently long paragraph (split by blank lines) becomes one or more audio files.
    """
    os.makedirs(output_dir, exist_ok=True)
    if device is None:
        # Auto-detect
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    pipeline = KPipeline(lang_code=lang_code, device=device)
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Replace single newlines (not part of double newline) with a space
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    if enforce_min_length:
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if len(p.strip()) >= MIN_TEXT_LENGTH]
    else:
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
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
        if progress_update:
            progress_update(i + 1)  # 1-based
    total_timer.print_elapsed("✅ All chunks")
    if progress_callback:
        progress_callback("✅ All chunks done!")

def process_pdf(
    pdf_path,
    output_dir="output",
    lang_code='a',
    voice='af_heart',
    progress_callback=None,
    chunk_callback=None,
    enforce_min_length=True,
    device=None,
    progress_update=None
):
    """
    Convert a PDF file to audio files (WAV) using Kokoro TTS.
    Each sufficiently long page becomes one or more audio files.
    """
    os.makedirs(output_dir, exist_ok=True)
    if device is None:
        # Auto-detect
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    pipeline = KPipeline(lang_code=lang_code, device=device)
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() for page in reader.pages]
    if enforce_min_length:
        valid_pages = [p.strip() for p in pages if p and len(p.strip()) >= MIN_TEXT_LENGTH]
    else:
        valid_pages = [p.strip() for p in pages if p and p.strip()]
    estimate_total(valid_pages, avg_seconds_per_chapter=15)

    total_timer = Timer()
    total_timer.start()

    for i, page_text in enumerate(valid_pages):
        if progress_callback:
            progress_callback(f"🔊 Processing page {i}")
        chunk_timer = Timer()
        chunk_timer.start()
        for j, (_, _, audio) in enumerate(pipeline(page_text, voice=voice, speed=1)):
            filename = f"{output_dir}/page_{i:02d}_{j}.wav"
            sf.write(filename, audio, 24000)
            if chunk_callback:
                chunk_callback(filename)
        chunk_timer.print_elapsed(f"✅ Done page {i}")
        if progress_update:
            progress_update(i + 1)  # 1-based
    total_timer.print_elapsed("✅ All pages")
    if progress_callback:
        progress_callback("✅ All pages done!")

if __name__ == "__main__":
    # CLI usage for backward compatibility (EPUB only)
    process_epub(
        book_path="input/gift.epub",
        output_dir="output",
        lang_code='a',
        voice='af_heart'
    )

