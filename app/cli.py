import argparse
import os

from processor import process_epub, process_txt, process_pdf
from merge_audio import merge_audio_files

def add_common(parser):
    parser.add_argument("--out", default="output", help="Output folder for WAVs/MP3")
    parser.add_argument("--lang", default="a", help="Language code (e.g., 'a' for English)")
    parser.add_argument("--voice", default="af_heart", help="Voice name")
    parser.add_argument("--merge", action="store_true", help="After generation, merge WAVs into MP3")
    parser.add_argument("--bitrate", default="64k", help="MP3 bitrate for merge (e.g., 64k, 96k, 128k)")
    parser.add_argument("--outfile", default=None, help="Output MP3 path (defaults to <out>/full_book.mp3)")

def main():
    parser = argparse.ArgumentParser(description="Kokoro: EPUB/TXT/PDF → WAV → MP3")
    sub = parser.add_subparsers(dest="command", required=True)

    # EPUB
    p_epub = sub.add_parser("epub", help="Convert EPUB to WAV (optionally merge to MP3)")
    p_epub.add_argument("book_path", help="Path to EPUB file")
    add_common(p_epub)

    # TXT
    p_txt = sub.add_parser("txt", help="Convert TXT to WAV (optionally merge to MP3)")
    p_txt.add_argument("txt_path", help="Path to TXT file")
    add_common(p_txt)

    # PDF
    p_pdf = sub.add_parser("pdf", help="Convert PDF to WAV (optionally merge to MP3)")
    p_pdf.add_argument("pdf_path", help="Path to PDF file")
    add_common(p_pdf)

    # MERGE only
    p_merge = sub.add_parser("merge", help="Merge existing WAVs into a single MP3")
    p_merge.add_argument("folder", help="Folder containing WAVs (e.g., output)")
    p_merge.add_argument("--outfile", default=None, help="MP3 output path (defaults to <folder>/full_book.mp3)")
    p_merge.add_argument("--bitrate", default="64k", help="MP3 bitrate (e.g., 64k, 96k, 128k)")

    args = parser.parse_args()

    if args.command == "epub":
        process_epub(args.book_path, output_dir=args.out, lang_code=args.lang, voice=args.voice)
        if args.merge:
            outmp3 = args.outfile or os.path.join(args.out, "full_book.mp3")
            merge_audio_files(folder=args.out, output_path=outmp3, bitrate=args.bitrate)

    elif args.command == "txt":
        process_txt(args.txt_path, output_dir=args.out, lang_code=args.lang, voice=args.voice)
        if args.merge:
            outmp3 = args.outfile or os.path.join(args.out, "full_book.mp3")
            merge_audio_files(folder=args.out, output_path=outmp3, bitrate=args.bitrate)

    elif args.command == "pdf":
        process_pdf(args.pdf_path, output_dir=args.out, lang_code=args.lang, voice=args.voice)
        if args.merge:
            outmp3 = args.outfile or os.path.join(args.out, "full_book.mp3")
            merge_audio_files(folder=args.out, output_path=outmp3, bitrate=args.bitrate)

    elif args.command == "merge":
        merge_audio_files(folder=args.folder, output_path=args.outfile, bitrate=args.bitrate)

if __name__ == "__main__":
    main()
