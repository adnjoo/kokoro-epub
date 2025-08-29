import re, time, tempfile
from pathlib import Path
import soundfile as sf
import torch
from kokoro import KPipeline

from utils import (
    extract_chapters,
    merge_to_mp3,
    merge_to_m4b,
    chapter_duration_ms,
    write_chapters_metadata,
)

SPLIT_PATTERN = r"\n{2,}"
SAMPLE_RATE = 24000
DEFAULT_LANG = "a"
DEFAULT_VOICE = "af_heart"


def epub_to_audio(epub_file, voice, speed, selected_titles, format_choice, progress=None):
    """
    Core generator that streams progress and yields (mp3_out, m4b_out, logs).
    Used by both Gradio and CLI.
    """
    start_time = time.time()
    workdir = tempfile.mkdtemp(prefix="kokoro_epub_")
    wav_dir = Path(workdir) / "wavs"
    wav_dir.mkdir(parents=True, exist_ok=True)

    logs = "🔎 Reading EPUB…"
    yield None, None, logs

    chapters = extract_chapters(epub_file.name)
    if not chapters:
        yield None, None, "❌ No chapters found."
        return

    if selected_titles:
        chapters = [
            (t, txt)
            for (t, txt) in chapters
            if f"{t} ({len(txt.split())} words)" in selected_titles
        ]

    # device
    if torch.cuda.is_available():
        device = "cuda"
        logs += f"\n✅ CUDA available: {torch.cuda.get_device_name(0)}"
    else:
        device = "cpu"
        logs += "\n⚠️ CUDA not available, using CPU."

    logs += f"\n🚀 Initializing Kokoro (device={device})…"
    yield None, None, logs

    pipeline = KPipeline(lang_code=DEFAULT_LANG, device=device)

    wav_paths = []
    chapter_durations = []
    part_idx = 0
    total = len(chapters)

    for ci, (title, text) in enumerate(chapters):
        chapter_start = time.time()
        logs += f"\n🔊 Starting {title} ({ci+1}/{total}) – {len(text.split())} words"
        yield None, None, logs

        chapter_wavs = []
        for _, _, audio in pipeline(
            text,
            voice=voice,
            speed=float(speed),
            split_pattern=SPLIT_PATTERN,
        ):
            safe_title = re.sub(r"[^a-zA-Z0-9]+", "_", title)[:30]
            wav_path = wav_dir / f"part_{part_idx:05d}_{safe_title}.wav"
            sf.write(str(wav_path), audio, SAMPLE_RATE)
            wav_paths.append(str(wav_path))
            chapter_wavs.append(str(wav_path))
            part_idx += 1

        if chapter_wavs:
            dur_ms = chapter_duration_ms(chapter_wavs)
            chapter_durations.append((title, dur_ms))

        logs += f"\n✅ Finished {title} in {time.time() - chapter_start:.2f}s"
        yield None, None, logs

    # outputs
    out_dir = Path(workdir)
    base_name = Path(epub_file.name).stem
    mp3_path = out_dir / f"{base_name}_{voice}.mp3"
    m4b_path = out_dir / f"{base_name}_{voice}.m4b"
    chapters_txt = out_dir / f"{base_name}_chapters.txt" if chapter_durations else None

    if chapter_durations:
        write_chapters_metadata(chapter_durations, chapters_txt)
        logs += f"\n📝 Chapters metadata saved ({chapters_txt.name})."

    if format_choice == "MP3":
        if merge_to_mp3(wav_paths, str(mp3_path)):
            logs += f"\n✅ MP3 created ({mp3_path.name})."
            logs += f"\n⏱️ Total time: {time.time() - start_time:.2f}s"
            yield str(mp3_path), None, logs
        else:
            yield None, None, "❌ Failed to merge MP3"

    elif format_choice == "M4B":
        if merge_to_m4b(wav_paths, str(m4b_path), chapters_txt):
            logs += f"\n📚 M4B created ({m4b_path.name})."
            logs += f"\n⏱️ Total time: {time.time() - start_time:.2f}s"
            yield None, str(m4b_path), logs
        else:
            yield None, None, "❌ Failed to merge M4B"
