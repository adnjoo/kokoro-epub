# kokoro-epub

> **Disclaimer:** Only use material from the public domain.

Convert EPUB, TXT, or PDF files to audio using Python and PyQt.

Works on **Windows** and **macOS**.

![Screenshot](assets/20250720-screen.png)

## Quick Start

```bash
# Setup
python3.11 -m venv kokoro-env
source kokoro-env/bin/activate
pip install -r requirements.txt

# Run
cd app
python pyqt_app.py
```

- The PyQt app lets you choose CPU or GPU (CUDA) for processing if you have an NVIDIA GPU and CUDA-enabled PyTorch installed. CUDA is much faster than CPU.
- `ffmpeg` is required for audio merging. On Windows, one way to install it is with `winget`.

## License

MIT License. See [LICENSE.md](./LICENSE.md).
