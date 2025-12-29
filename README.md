---
title: Kokoro Epub
emoji: 💻
colorFrom: red
colorTo: gray
sdk: gradio
sdk_version: 5.44.0
app_file: app.py
pinned: false
short_description: epub 2 mp3 / m4b
---

# kokoro-epub

> [!IMPORTANT]
**This tool is intended for use with non-DRM, legally acquired eBooks only.** <br>
The authors are not responsible for any misuse of this software or any resulting legal consequences. <br>

Converts EPUB to audiobook (MP3 or M4B (chapter markers)) using python.

[Sponsor me on GitHub](https://github.com/sponsors/adnjoo)

<img src='public/20250828.png' width='400'>

## Quick Start

```bash
# Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# System requirement for MP3/M4B merge
sudo apt install ffmpeg -y    # required for pydub exports

# Run
python app.py
```

👉 Try it free on [Hugging Face Space](https://huggingface.co/spaces/adnjoo/kokoro-epub) — or run faster in the cloud at [bookbearai.com](https://bookbearai.com).

### GPU Torch

Gutenberg Kafka - The Metamorphosis 25152 words ~ 100 pages ~ 60mb (MP3 2h12m • 64 kbps • 24 kHz • mono)

5060 Ti 16GB - ETA 194s/3' | WPS 130
vs
CPU - 1389s/23' | WPS 18

```bash
 pip install --upgrade torch --index-url https://download.pytorch.org/whl/cu128
```

### CLI Usage

In addition to the Gradio UI, you can also run the tool directly from the command line with `cli.py`:

List chapters in an EPUB:
```bash
python cli.py 5200.epub --list-chapters
````

Convert to M4B, selecting only chapters II and III:

```bash
python cli.py 5200.epub --format M4B --chapters 3,4 --out audiobooks
```


## Sample Output

<video src='https://github.com/user-attachments/assets/cd229d05-e59a-4e91-becf-4b3de1859607
' width=180></video>

## Related Projects

If you're exploring other ebook-to-audio solutions, you might also check out:  
- [readest](https://github.com/readest/readest) - modern e-reader with Edge TTS (22 voices)
- [audiblez](https://github.com/santinic/audiblez) — CLI tool for converting text to audiobooks.  
- [ebook2audiobook](https://github.com/DrewThomasson/ebook2audiobook) — Simple Python-based ebook-to-audio converter.  

## License

MIT License. See [LICENSE.md](./LICENSE.md).


## Contributing

📌 See [CONTRIBUTING.md](./CONTRIBUTING.md) if you'd like to contribute.
