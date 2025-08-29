import argparse, sys
from pathlib import Path
from pipeline import epub_to_audio, extract_chapters, DEFAULT_VOICE

def main():
    parser = argparse.ArgumentParser(description="EPUB → Audiobook CLI")
    parser.add_argument("epub", help="Path to EPUB file")
    parser.add_argument("--out", default="output", help="Output directory")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="Voice (default af_heart)")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier")
    parser.add_argument("--format", choices=["MP3","M4B"], default="MP3", help="Output format")
    parser.add_argument("--list-chapters", action="store_true", help="List chapters and exit")
    parser.add_argument("--chapters", help="Comma-separated chapter titles to convert", default=None)
    args = parser.parse_args()

    epub_path = Path(args.epub)
    chapters = extract_chapters(str(epub_path))

    # Dry run
    if args.list_chapters:
        print(f"\n📖 {epub_path.name} — {len(chapters)} chapters found:\n")
        for i, (title, text) in enumerate(chapters, 1):
            print(f"{i:02d}. {title} ({len(text.split())} words)")
        sys.exit(0)

    # After parsing args and extracting chapters...
    selected = []
    if args.chapters:
        parts = [c.strip() for c in args.chapters.split(",")]
        for p in parts:
            if p.isdigit():
                idx = int(p) - 1
                if 0 <= idx < len(chapters):
                    selected.append(f"{chapters[idx][0]} ({len(chapters[idx][1].split())} words)")
            else:
                selected.append(p)

    result_file = None
    last_logs = ""
    for mp3_out, m4b_out, logs in epub_to_audio(
        epub_path.open("rb"),
        args.voice,
        args.speed,
        selected,
        args.format.upper(),
    ):
        if logs and logs != last_logs:
            diff = logs[len(last_logs):]
            if diff.strip():
                for line in diff.strip().splitlines():
                    print("   " + line)
            last_logs = logs

        if mp3_out or m4b_out:
            result_file = mp3_out or m4b_out

    print(f"\n✅ Audiobook ready: {result_file}")

if __name__ == "__main__":
    main()
