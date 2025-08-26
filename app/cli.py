# cli.py
import argparse
import os
import sys
from processor import process_epub, process_txt, process_pdf, DEFAULT_LANG_CODE, DEFAULT_VOICE
from merge_audio import merge_audio_files

def positive_int(v):
    try:
        i = int(v)
        if i < 0:
            raise ValueError
        return i
    except:
        raise argparse.ArgumentTypeError("must be a non-negative integer")

def main():
    p = argparse.ArgumentParser(description="Headless kokoro-epub runner")
    p.add_argument("--input", "-i", required=True, help="Path to input file (.epub | .txt | .pdf)")
    p.add_argument("--outdir", "-o", default="output", help="Output directory for WAV/MP3")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto", help="Force device")
    p.add_argument("--lang", default=DEFAULT_LANG_CODE, help="Kokoro lang code (e.g., 'a' English, 'e' Spanish)")
    p.add_argument("--voice", default=DEFAULT_VOICE, help="Kokoro voice (e.g., 'af_heart')")
    p.add_argument("--start-chapter", type=positive_int, default=0, help="EPUB: start chapter index")
    p.add_argument("--no-min-length", action="store_true", help="Disable MIN_TEXT_LENGTH filtering")
    p.add_argument("--bitrate", default="64k", help="Final MP3 bitrate (e.g., 64k/96k/128k)")
    args = p.parse_args()

    in_path = args.input
    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)

    # Resolve device
    device = None
    if args.device != "auto":
        device = args.device

    # Simple progress prints (keeps logs useful in ephemeral jobs)
    def log(msg):
        print(msg, flush=True)

    ext = os.path.splitext(in_path)[1].lower()
    enforce_min_length = not args.no_min_length

    if ext == ".epub":
        process_epub(
            book_path=in_path,
            output_dir=outdir,
            lang_code=args.lang,
            voice=args.voice,
            start_chapter=args.start_chapter,
            progress_callback=log,
            chapter_callback=lambda f: log(f"✔ wrote {f}"),
            enforce_min_length=enforce_min_length,
            device=device,
            progress_update=lambda n: log(f"progress: {n}")
        )
    elif ext == ".txt":
        process_txt(
            txt_path=in_path,
            output_dir=outdir,
            lang_code=args.lang,
            voice=args.voice,
            progress_callback=log,
            chunk_callback=lambda f: log(f"✔ wrote {f}"),
            enforce_min_length=enforce_min_length,
            device=device,
            progress_update=lambda n: log(f"progress: {n}")
        )
    elif ext == ".pdf":
        process_pdf(
            pdf_path=in_path,
            output_dir=outdir,
            lang_code=args.lang,
            voice=args.voice,
            progress_callback=log,
            chunk_callback=lambda f: log(f"✔ wrote {f}"),
            enforce_min_length=enforce_min_length,
            device=device,
            progress_update=lambda n: log(f"progress: {n}")
        )
    else:
        print(f"Unsupported file type: {ext}", file=sys.stderr)
        sys.exit(2)

    # Merge to MP3
    ok = merge_audio_files(folder=outdir, output_path=os.path.join(outdir, "full_book.mp3"), bitrate=args.bitrate, progress_callback=log)
    if not ok:
        sys.exit(3)
    print("✅ Done.")

if __name__ == "__main__":
    main()
