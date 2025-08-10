# kokoro-epub

> **Disclaimer:** Only use material from the public domain.

Convert EPUB, TXT, or PDF files to audio using Python and PyQt.

Works on **Windows** and **macOS**.

![Screenshot](assets/20250720-screen.png)

## Quick Start

```bash
# Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
cd app
python pyqt_app.py
```

## Sample Output

<video src='https://github.com/user-attachments/assets/cd229d05-e59a-4e91-becf-4b3de1859607
' width=180></video>

Spanish Example:

<video src='https://github.com/user-attachments/assets/6f9f8295-ba3e-4e00-97bf-7b94e740c2b1' width=180></video>

- The PyQt app lets you choose CPU or GPU (CUDA) for processing if you have an NVIDIA GPU and CUDA-enabled PyTorch installed. CUDA is much faster than CPU.
- `ffmpeg` is required for audio merging. On Windows, one way to install it is with `winget`.

# Docker
```bash
docker build -t kokoro-cuda-test .
docker run --gpus all kokoro-cuda-test
```

## License

MIT License. See [LICENSE.md](./LICENSE.md).
