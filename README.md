## Setup

Before running any scripts, create and activate a virtual environment:

```bash
python3.11 -m venv kokoro-env  # Python 3.13 doesn't work

# Activate the virtual environment
source kokoro-env/bin/activate     # macOS/Linux
# or
source kokoro-env/Scripts/activate  # Windows/Git Bash

# Install dependencies
pip install -r requirements.txt
```

---

## Requirements

### Python Packages

* All listed in `requirements.txt`

### System Dependencies

* [`ffmpeg`](https://ffmpeg.org/) — required by some TTS modules

#### Example (macOS):

```bash
brew install ffmpeg
```


## Training

- https://github.com/idiap/coqui-ai-TTS

---

## License

This project is licensed under the [MIT License](./LICENSE).

## Running the Desktop App

To launch the PyQt desktop application:

```bash
cd app
python pyqt_app.py
```

This will open a window where you can drag and drop EPUB, TXT, or PDF files to generate audio files.

## Build

```bash
pyinstaller pyqt_app.spec
```