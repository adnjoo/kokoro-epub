import argparse, sys
from pathlib import Path
import shutil
from pipeline import epub_to_audio, extract_chapters, DEFAULT_VOICE

def parse_chapters(chapters_arg: str, total: int):
    """Parse chapter selections like '1,5,7-10,15' or '3-' or '-5'."""
    chapters = set()
    for part in chapters_arg.split(","):
        part = part.strip()
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = int(start_str) if start_str else 1
            end = int(end_str) if end_str else total
            chapters.update(range(start, end + 1))
        elif part.isdigit():
            chapters.add(int(part))
        else:
            # fallback: allow title text matching
            chapters.add(part)
    return sorted(chapters)

def main():
    parser = argparse.ArgumentParser(description="EPUB → Audiobook CLI")
    parser.add_argument("epub", help="Path to EPUB file")
    parser.add_argument("--out", default="output", help="Output directory")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="Voice (default af_heart)")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier")
    parser.add_argument("--format", choices=["MP3","M4B"], default="MP3", help="Output format")
    parser.add_argument("--list-chapters", action="store_true", help="List chapters and exit")
    parser.add_argument("--chapters", help="Comma-separated chapter numbers or ranges to convert", default=None)
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
        parsed = parse_chapters(args.chapters, len(chapters))
        for p in parsed:
            if isinstance(p, int):
                idx = p - 1
                if 0 <= idx < len(chapters):
                    title, text = chapters[idx]
                    selected.append(f"{title} ({len(text.split())} words)")
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
        cli=True,
    ):
        if logs and logs != last_logs:
            diff = logs[len(last_logs):]
            if diff.strip():
                for line in diff.strip().splitlines():
                    print("   " + line)
            last_logs = logs
        
        if mp3_out or m4b_out:
            tmp_result = Path(mp3_out or m4b_out)
            out_dir = Path(args.out)
            out_dir.mkdir(parents=True, exist_ok=True)

            # Rebuild filename in final output dir
            final_path = out_dir / tmp_result.name
            shutil.copy(tmp_result, final_path)
            result_file = final_path

    print(f"\n✅ Audiobook ready: {result_file}")

if __name__ == "__main__":
    main()
