import argparse
from processor import process_epub, process_txt, process_pdf

def main():
    parser = argparse.ArgumentParser(description="Kokoro EPUB/TXT/PDF → Audio")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # EPUB
    epub_parser = subparsers.add_parser("epub", help="Convert EPUB to WAV")
    epub_parser.add_argument("book_path", help="Path to EPUB file")
    epub_parser.add_argument("--out", default="output", help="Output folder")
    epub_parser.add_argument("--lang", default="a", help="Language code")
    epub_parser.add_argument("--voice", default="af_heart", help="Voice")

    # TXT
    txt_parser = subparsers.add_parser("txt", help="Convert TXT to WAV")
    txt_parser.add_argument("txt_path", help="Path to TXT file")
    txt_parser.add_argument("--out", default="output", help="Output folder")
    txt_parser.add_argument("--lang", default="a", help="Language code")
    txt_parser.add_argument("--voice", default="af_heart", help="Voice")

    # PDF
    pdf_parser = subparsers.add_parser("pdf", help="Convert PDF to WAV")
    pdf_parser.add_argument("pdf_path", help="Path to PDF file")
    pdf_parser.add_argument("--out", default="output", help="Output folder")
    pdf_parser.add_argument("--lang", default="a", help="Language code")
    pdf_parser.add_argument("--voice", default="af_heart", help="Voice")

    args = parser.parse_args()

    if args.command == "epub":
        process_epub(args.book_path, output_dir=args.out, lang_code=args.lang, voice=args.voice)
    elif args.command == "txt":
        process_txt(args.txt_path, output_dir=args.out, lang_code=args.lang, voice=args.voice)
    elif args.command == "pdf":
        process_pdf(args.pdf_path, output_dir=args.out, lang_code=args.lang, voice=args.voice)

if __name__ == "__main__":
    main()
