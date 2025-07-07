# Vibetails

A desktop application that converts EPUB, TXT, or PDF files into audio using advanced TTS (Text-to-Speech) technology. Built with Python and PyQt, Vibetails makes it easy to generate high-quality audio from your reading materials.

---

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [Build](#build)
- [License](#license)
- [Contributing](#contributing)

---

## Features
- Drag-and-drop interface for EPUB, TXT, and PDF files
- Converts text files to audio using TTS
- Output audio files saved automatically
- Cross-platform (macOS, Windows, Linux)

---

## Requirements

### Python
- Python 3.11 (Python 3.13 is not supported)

### Python Packages
- All dependencies are listed in `requirements.txt`

### System Dependencies
- [`ffmpeg`](https://ffmpeg.org/) — required by some TTS modules

#### Example (macOS):
```bash
brew install ffmpeg
```

---

## Setup

1. **Create and activate a virtual environment:**
   ```bash
   python3.11 -m venv kokoro-env
   source kokoro-env/bin/activate     # macOS/Linux
   # or
   source kokoro-env/Scripts/activate  # Windows/Git Bash
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### Launch the Desktop App

```bash
cd app
python pyqt_app.py
```

- The application window will open.
- Drag and drop your EPUB, TXT, or PDF files into the window.
- The app will generate audio files and save them in the output directory.

---

## Build

To create a standalone executable:

```bash
pyinstaller pyqt_app.spec
```

To build a DMG (macOS disk image):

```bash
bash build.sh
```

---

## License

This project is licensed under the [MIT License](./LICENSE.md).

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
