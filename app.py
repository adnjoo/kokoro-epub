import gradio as gr
import os, re, tempfile, shutil, time
from pathlib import Path

# EPUB parsing + text cleanup
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup

# TTS + audio I/O
from kokoro import KPipeline
import soundfile as sf

# Torch
import torch

from extract_chapters import extract_chapters

# Optional merge to MP3 (requires ffmpeg on the system)
try:
    from pydub import AudioSegment
    HAVE_PYDUB = True
except Exception:
    HAVE_PYDUB = False

MIN_TEXT_LENGTH = 100
SPLIT_PATTERN = r"\n{2,}"      # split on blank-line paragraphs
SAMPLE_RATE = 24000
DEFAULT_LANG = "a"             # Kokoro English
DEFAULT_VOICE = "af_heart"     # Kokoro English female

def _merge_to_mp3(wav_paths, out_mp3_path, bitrate="64k"):
    if not HAVE_PYDUB or shutil.which("ffmpeg") is None:
        return False
    combined = AudioSegment.silent(duration=0)
    for w in wav_paths:
        combined += AudioSegment.from_wav(w)
    combined.export(out_mp3_path, format="mp3", bitrate=bitrate)
    return True


def epub_to_audio(epub_file, voice, speed, progress=gr.Progress()):
    """Gradio generator: yields (file, logs) progressively, with progress bar updates."""
    if epub_file is None:
        yield None, "Please upload an EPUB."
        return

    start_time = time.time()   # 🕒 start stopwatch once

    workdir = tempfile.mkdtemp(prefix="kokoro_epub_")
    wav_dir = Path(workdir) / "wavs"
    wav_dir.mkdir(parents=True, exist_ok=True)

    logs = "🔎 Reading EPUB…"
    yield None, logs

    try:
        chapters = extract_chapters(epub_file.name)
        if not chapters:
            yield None, "No sufficiently long chapters found (MIN_TEXT_LENGTH=100)."
            return

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
        yield None, logs

        pipeline = KPipeline(lang_code=DEFAULT_LANG, device=device)

        wav_paths = []
        part_idx = 0
        total = len(chapters)
        for ci, (title, text) in enumerate(chapters):
            progress((ci + 1) / total, desc=f"Processing {title} ({ci+1}/{total})")
            logs += f"\n🔊 {title} ({ci+1}/{total})"
            yield None, logs

            for _, _, audio in pipeline(
                text,
                voice=voice,
                speed=float(speed),
                split_pattern=SPLIT_PATTERN,
            ):
                wav_path = wav_dir / f"part_{ci:03d}_{title}.wav"
                sf.write(str(wav_path), audio, SAMPLE_RATE)
                wav_paths.append(str(wav_path))

        out_dir = Path(workdir)
        out_mp3 = out_dir / "audiobook.mp3"
        if _merge_to_mp3(wav_paths, str(out_mp3)):
            logs += f"\n✅ MP3 created ({out_mp3.name})."
            total_time = time.time() - start_time
            logs += f"\n⏱️ Total time: {total_time:.2f} seconds"
            yield str(out_mp3), logs
        else:
            zip_base = out_dir / "audiobook_wavs"
            zip_path = shutil.make_archive(str(zip_base), "zip", wav_dir)
            total_time = time.time() - start_time
            logs += "\nℹ️ ffmpeg not found — returning WAVs as ZIP."
            logs += f"\n⏱️ Total time: {total_time:.2f} seconds"
            yield zip_path, logs

    except Exception as e:
        yield None, f"❌ Error: {e}"


# ---------------- Gradio UI ---------------- #

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

    with gr.Row():
        voice = gr.Dropdown(
            label="Voice",
            value=DEFAULT_VOICE,
            choices=[
                "af_heart",
                "af_alloy",
                "af_bella",
                "af_rose",
                "am_michael",
                "am_adam",
                "am_mandarin",
            ],
        )
        speed = gr.Slider(0.7, 1.3, value=1.0, step=0.05, label="Speed")

    run_btn = gr.Button("Convert")
    audio_out = gr.File(label="Download MP3 (or ZIP of WAVs)")
    logs = gr.Textbox(label="Logs", lines=12)

    run_btn.click(
        fn=epub_to_audio,
        inputs=[epub_in, voice, speed],
        outputs=[audio_out, logs],
    )

if __name__ == "__main__":
    print("Compiled CUDA version:", torch.version.cuda)
    print("Is CUDA available?:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("Current CUDA device index:", torch.cuda.current_device())
        print("Current CUDA device name:", torch.cuda.get_device_name(0))
    else:
        print("CUDA is not available. Skipping device info.")

    demo.launch()
