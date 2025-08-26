import gradio as gr
import os, re, tempfile, shutil
from pathlib import Path

# EPUB parsing + text cleanup
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup

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

MIN_TEXT_LENGTH = 100
SPLIT_PATTERN = r"\n{2,}"      # split on blank-line paragraphs
SAMPLE_RATE = 24000
DEFAULT_LANG = "a"             # Kokoro English
DEFAULT_VOICE = "af_heart"     # Kokoro English female


def _extract_epub_chapters(epub_path: str):
    book = epub.read_epub(epub_path)
    chapters = []
    for item in book.items:
        if item.get_type() == ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text(separator="\n").strip()
            # normalize: single newlines -> space (keep double newlines as paragraph breaks)
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
            if len(text) >= MIN_TEXT_LENGTH:
                chapters.append(text)
    return chapters


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

    workdir = tempfile.mkdtemp(prefix="kokoro_epub_")
    wav_dir = Path(workdir) / "wavs"
    wav_dir.mkdir(parents=True, exist_ok=True)

    logs = "🔎 Reading EPUB…"
    yield None, logs

    try:
        chapters = _extract_epub_chapters(epub_file.name)
        if not chapters:
            yield None, "No sufficiently long chapters found (MIN_TEXT_LENGTH=100)."
            return

        # pick device automatically
        try:
            if torch.cuda.is_available():
                device = "cuda"
                logs += f"\n✅ CUDA available: {torch.cuda.get_device_name(0)} (memory {torch.cuda.get_device_properties(0).total_memory // (1024**2)} MB)"
            else:
                device = "cpu"
                logs += "\n CUDA not available, using CPU."
        except Exception as e:
            device = "cpu"
            logs += f"\n torch not found or error checking CUDA: {e}"


        logs += f"\n🚀 Initializing Kokoro (device={device})…"
        yield None, logs

        pipeline = KPipeline(lang_code=DEFAULT_LANG, device=device)

        wav_paths = []
        part_idx = 0
        total = len(chapters)

        for ci, chapter in enumerate(chapters):
            # ✅ progress bar update
            progress((ci + 1) / total, desc=f"Processing chapter {ci+1}/{total}")
            logs += f"\n🔊 Chapter {ci+1}/{total}"
            yield None, logs

            for _, _, audio in pipeline(
                chapter,
                voice=voice,
                speed=float(speed),
                split_pattern=SPLIT_PATTERN,
            ):
                wav_path = wav_dir / f"part_{part_idx:05d}.wav"
                sf.write(str(wav_path), audio, SAMPLE_RATE)
                wav_paths.append(str(wav_path))
                part_idx += 1

        # Try to merge to MP3; else zip WAVs
        out_dir = Path(workdir)
        out_mp3 = out_dir / "audiobook.mp3"
        if _merge_to_mp3(wav_paths, str(out_mp3)):
            logs += f"\n✅ MP3 created ({out_mp3.name})."
            yield str(out_mp3), logs
        else:
            zip_base = out_dir / "audiobook_wavs"
            zip_path = shutil.make_archive(str(zip_base), "zip", wav_dir)
            logs += "\nℹ️ ffmpeg not found — returning WAVs as ZIP."
            yield zip_path, logs

    except Exception as e:
        yield None, f"❌ Error: {e}"


# ---------------- Gradio UI ---------------- #

with gr.Blocks(title="EPUB → MP3 (Kokoro)") as demo:
    gr.Markdown(
        "## EPUB → MP3 with Kokoro TTS\n"
        "Upload an EPUB and get a single MP3 (or a ZIP of WAVs if ffmpeg isn’t available)."
    )

    with gr.Row():
        epub_in = gr.File(label="EPUB file", file_types=[".epub"])

    with gr.Row():
        voice = gr.Dropdown(
            label="Voice",
            value=DEFAULT_VOICE,
            choices=[
                "af_heart",  # popular English female
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
    print("Current CUDA device index:", torch.cuda.current_device())
    print("Current CUDA device name:", torch.cuda.get_device_name(0))

    demo.launch()
