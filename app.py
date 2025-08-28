import gradio as gr
import os, re, tempfile, shutil, time
from pathlib import Path
from kokoro import KPipeline
import soundfile as sf
import torch

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


# ---------------- MAIN PIPELINE ---------------- #

def epub_to_audio(epub_file, voice, speed, selected_titles, format_choice, progress=gr.Progress()):
    if epub_file is None:
        yield (
            gr.update(value=None, visible=False),  # MP3
            gr.update(value=None, visible=False),  # M4B
            "Please upload an EPUB."
        )
        return

    start_time = time.time()
    workdir = tempfile.mkdtemp(prefix="kokoro_epub_")
    wav_dir = Path(workdir) / "wavs"
    wav_dir.mkdir(parents=True, exist_ok=True)

    logs = "🔎 Reading EPUB…"
    yield (
        gr.update(value=None, visible=False),
        gr.update(value=None, visible=False),
        logs
    )

    try:
        chapters = extract_chapters(epub_file.name)
        if not chapters:
            yield (
                gr.update(value=None, visible=False),
                gr.update(value=None, visible=False),
                "No chapters found."
            )
            return

        if selected_titles:
            chapters = [
                (t, txt)
                for (t, txt) in chapters
                if f"{t} ({len(txt.split())} words)" in selected_titles
            ]

        # device
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
        yield (
            gr.update(value=None, visible=False),
            gr.update(value=None, visible=False),
            logs
        )

        pipeline = KPipeline(lang_code=DEFAULT_LANG, device=device)

        wav_paths = []
        chapter_durations = []
        part_idx = 0
        total = len(chapters)

        for ci, (title, text) in enumerate(chapters):
            chapter_start = time.time()
            logs += f"\n🔊 Starting {title} ({ci+1}/{total}) – {len(text.split())} words"
            yield (
                gr.update(value=None, visible=False),
                gr.update(value=None, visible=False),
                logs
            )

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
            yield (
                gr.update(value=None, visible=False),
                gr.update(value=None, visible=False),
                logs
            )

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
                yield (
                    gr.update(value=str(mp3_path), visible=True),
                    gr.update(value=None, visible=False),
                    logs
                )
            else:
                zip_base = out_dir / "audiobook_wavs"
                zip_path = shutil.make_archive(str(zip_base), "zip", wav_dir)
                logs += "\nℹ️ ffmpeg not found — returning WAVs as ZIP."
                yield (
                    gr.update(value=zip_path, visible=True),
                    gr.update(value=None, visible=False),
                    logs
                )

        elif format_choice == "M4B":
            if merge_to_m4b(wav_paths, str(m4b_path), chapters_txt):
                logs += f"\n📚 M4B created ({m4b_path.name})."
                logs += f"\n⏱️ Total time: {time.time() - start_time:.2f}s"
                yield (
                    gr.update(value=None, visible=False),
                    gr.update(value=str(m4b_path), visible=True),
                    logs
                )
            else:
                zip_base = out_dir / "audiobook_wavs"
                zip_path = shutil.make_archive(str(zip_base), "zip", wav_dir)
                logs += "\nℹ️ ffmpeg not found — returning WAVs as ZIP."
                yield (
                    gr.update(value=zip_path, visible=True),
                    gr.update(value=None, visible=False),
                    logs
                )

    except Exception as e:
        yield (
            gr.update(value=None, visible=False),
            gr.update(value=None, visible=False),
            f"❌ Error: {e}"
        )


# ---------------- GRADIO UI ---------------- #

with gr.Blocks(title="kokoro-epub — Free EPUB → Audiobook") as demo:
    gr.Markdown("## Free EPUB → Audiobook (Open Source)")

    epub_in = gr.File(label="EPUB file", file_types=[".epub"])
    chapter_selector = gr.CheckboxGroup(label="Select chapters to convert", choices=[])
    epub_in.change(
        fn=lambda f: gr.update(
            choices=[f"{t} ({len(txt.split())} words)" for (t, txt) in extract_chapters(f.name)] if f else []
        ),
        inputs=epub_in,
        outputs=chapter_selector,
    )

    with gr.Row():
        voice = gr.Dropdown(
            label="Voice",
            value=DEFAULT_VOICE,
            choices=["af_heart", "af_alloy", "af_bella", "af_rose", "am_michael", "am_adam", "am_mandarin"],
        )
        speed = gr.Slider(0.7, 1.3, value=1.0, step=0.05, label="Speed")
        format_choice = gr.Radio(label="Output format", choices=["MP3", "M4B"], value="MP3")

    run_btn = gr.Button("Convert")
    audio_out = gr.File(label="Download MP3 (or ZIP)", visible=False)
    m4b_out = gr.File(label="Download M4B (with chapters)", visible=False)
    logs = gr.Textbox(label="Logs", lines=12)

    run_btn.click(
        fn=epub_to_audio,
        inputs=[epub_in, voice, speed, chapter_selector, format_choice],
        outputs=[audio_out, m4b_out, logs],
    )


if __name__ == "__main__":
    demo.launch()
