import gradio as gr
import os, re, tempfile, shutil, time
from pathlib import Path

# EPUB parsing
from utils.extract_chapters import extract_chapters

# TTS + audio I/O
from kokoro import KPipeline
import soundfile as sf

# Torch
import torch

# Optional merge to MP3 (requires ffmpeg on the system)
try:
    from pydub import AudioSegment
    HAVE_PYDUB = True
except Exception:
    HAVE_PYDUB = False

SPLIT_PATTERN = r"\n{2,}"      # split on blank-line paragraphs
SAMPLE_RATE = 24000
DEFAULT_LANG = "a"             # Kokoro English
DEFAULT_VOICE = "af_heart"     # Kokoro English female


# ---------------- HELPERS ---------------- #

def _merge_to_mp3(wav_paths, out_mp3_path, bitrate="64k"):
    """Merge WAVs into a single MP3 using pydub/ffmpeg."""
    if not HAVE_PYDUB or shutil.which("ffmpeg") is None:
        return False
    combined = AudioSegment.silent(duration=0)
    for w in wav_paths:
        combined += AudioSegment.from_wav(w)
    combined.export(out_mp3_path, format="mp3", bitrate=bitrate)
    return True


def _write_chapters_metadata(chapter_durations, out_txt):
    """Write ffmpeg-style chapters.txt from [(title, dur_ms), ...]."""
    offset = 0
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(";FFMETADATA1\n")
        for title, dur in chapter_durations:
            start = offset
            end = offset + dur
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={start}\n")
            f.write(f"END={end}\n")
            f.write(f"title={title}\n\n")
            offset = end


def list_chapter_titles(epub_file):
    if epub_file is None:
        return gr.update(choices=[])
    chapters = extract_chapters(epub_file.name)
    titles = [f"{t} ({len(txt.split())} words)" for (t, txt) in chapters]
    return gr.update(choices=titles, value=titles)


# ---------------- MAIN PIPELINE ---------------- #

def epub_to_audio(epub_file, voice, speed, selected_titles, progress=gr.Progress()):
    """Convert EPUB chapters into audiobook MP3, filtering by user selection."""
    if epub_file is None:
        yield None, None, "Please upload an EPUB."
        return

    start_time = time.time()
    workdir = tempfile.mkdtemp(prefix="kokoro_epub_")
    wav_dir = Path(workdir) / "wavs"
    wav_dir.mkdir(parents=True, exist_ok=True)

    logs = "🔎 Reading EPUB…"
    yield None, None, logs

    try:
        chapters = extract_chapters(epub_file.name)
        if not chapters:
            yield None, None, "No chapters found."
            return

        if selected_titles:
            chapters = [
                (t, txt)
                for (t, txt) in chapters
                if f"{t} ({len(txt.split())} words)" in selected_titles
            ]

        # Pick device
        try:
            if torch.cuda.is_available():
                device = "cuda"
                logs += f"\n✅ CUDA available: {torch.cuda.get_device_name(0)}"
            else:
                device = "cpu"
                logs += "\n CUDA not available, using CPU."
        except Exception as e:
            device = "cpu"
            logs += f"\n torch error checking CUDA: {e}"

        logs += f"\n🚀 Initializing Kokoro (device={device})…"
        yield None, None, logs

        pipeline = KPipeline(lang_code=DEFAULT_LANG, device=device)

        wav_paths = []
        part_idx = 0
        total = len(chapters)
        chapter_durations = []

        # Generate audio per chapter
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

            if HAVE_PYDUB:
                dur_ms = sum(len(AudioSegment.from_wav(w)) for w in chapter_wavs)
                chapter_durations.append((title, dur_ms))

            chapter_elapsed = time.time() - chapter_start
            logs += f"\n✅ Finished {title} in {chapter_elapsed:.2f}s"
            yield None, None, logs

        # Merge to MP3
        out_dir = Path(workdir)
        base_name = Path(epub_file.name).stem
        out_name = f"{base_name}_{voice}.mp3"
        out_mp3 = out_dir / out_name
        chapters_txt = None

        if _merge_to_mp3(wav_paths, str(out_mp3)):
            logs += f"\n✅ MP3 created ({out_mp3.name})."

            if chapter_durations:
                chapters_txt = out_dir / f"{base_name}_chapters.txt"
                _write_chapters_metadata(chapter_durations, chapters_txt)
                logs += f"\n📝 Chapters metadata saved ({chapters_txt.name})."

            total_time = time.time() - start_time
            logs += f"\n⏱️ Total time: {total_time:.2f} seconds"
            yield str(out_mp3), str(chapters_txt) if chapters_txt else None, logs
        else:
            zip_base = out_dir / "audiobook_wavs"
            zip_path = shutil.make_archive(str(zip_base), "zip", wav_dir)
            total_time = time.time() - start_time
            logs += "\nℹ️ ffmpeg not found — returning WAVs as ZIP."
            logs += f"\n⏱️ Total time: {total_time:.2f} seconds"
            yield zip_path, None, logs

    except Exception as e:
        yield None, None, f"❌ Error: {e}"


# ---------------- GRADIO UI ---------------- #

with gr.Blocks(title="BookBearAI — Free EPUB → MP3") as demo:
    gr.Markdown(
        "## Free EPUB → MP3 (Open Source)\n"
        "Upload any non-DRM EPUB and generate a natural-sounding AI audiobook (MP3).\n\n"
        "This free demo is powered by [Kokoro TTS](https://github.com/hexgrad/kokoro-tts) "
        "and is part of the open-source project at [github.com/adnjoo/kokoro-epub](https://github.com/adnjoo/kokoro-epub).\n\n"
        "**Want more voices, formats (PDF, TXT), and cloud hosting?** "
        "Check out [BookBearAI](https://bookbearai.com) → our full platform for ebook-to-audiobook conversion."
    )

    with gr.Row():
        epub_in = gr.File(label="EPUB file", file_types=[".epub"])

    chapter_selector = gr.CheckboxGroup(label="Select chapters to convert", choices=[])

    epub_in.change(
        fn=list_chapter_titles,
        inputs=epub_in,
        outputs=chapter_selector
    )

    with gr.Row():
        voice = gr.Dropdown(
            label="Voice",
            value=DEFAULT_VOICE,
            choices=["af_heart","af_alloy","af_bella","af_rose","am_michael","am_adam","am_mandarin"],
        )
        speed = gr.Slider(0.7, 1.3, value=1.0, step=0.05, label="Speed")

    run_btn = gr.Button("Convert")
    audio_out = gr.File(label="Download MP3 (or ZIP of WAVs)")
    chapters_out = gr.File(label="Download Chapters Metadata")
    logs = gr.Textbox(label="Logs", lines=12)

    run_btn.click(
        fn=epub_to_audio,
        inputs=[epub_in, voice, speed, chapter_selector],
        outputs=[audio_out, chapters_out, logs],
    )


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    print("Compiled CUDA version:", torch.version.cuda)
    print("Is CUDA available?:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("Current CUDA device index:", torch.cuda.current_device())
        print("Current CUDA device name:", torch.cuda.get_device_name(0))
    else:
        print("CUDA is not available. Skipping device info.")

    demo.launch()
