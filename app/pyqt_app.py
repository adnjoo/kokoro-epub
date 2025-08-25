import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QProgressBar, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from merge_audio import merge_audio_files
import glob
from processor import process_epub, process_txt, process_pdf, MIN_TEXT_LENGTH
from PyPDF2 import PdfReader


class Worker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    progress_value = pyqtSignal(int)
    progress_max = pyqtSignal(int)

    def __init__(self, file_path, output_dir, enforce_min_length=True, device=None, lang_code='a', voice='af_heart'):
        super().__init__()
        self.file_path = file_path
        self.output_dir = output_dir
        self._is_stopped = False
        self.enforce_min_length = enforce_min_length
        self.device = device
        self.lang_code = lang_code
        self.voice = voice

    def run(self):
        ext = os.path.splitext(self.file_path)[1].lower()
        self.progress.emit(f"Processing: {os.path.basename(self.file_path)}")
        try:
            if ext == '.epub':
                book = epub.read_epub(self.file_path)
                chapters = [item for item in book.items if item.get_type() == ITEM_DOCUMENT]
                valid_chapters = [
                    chapter for chapter in chapters
                    if len(BeautifulSoup(chapter.get_content(), 'html.parser').get_text().strip()) >= 100
                ]
                total = len(valid_chapters)
                self.progress_max.emit(total if total > 0 else 1)
                def progress_update(current):
                    self.progress_value.emit(current)
                process_epub(
                    self.file_path,
                    self.output_dir,
                    progress_callback=self.progress.emit,
                    enforce_min_length=self.enforce_min_length,
                    device=self.device,
                    progress_update=progress_update,
                    lang_code=self.lang_code,
                    voice=self.voice
                )
            elif ext == '.txt':
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) >= 100]
                total = len(paragraphs)
                self.progress_max.emit(total if total > 0 else 1)
                def progress_update(current):
                    self.progress_value.emit(current)
                process_txt(
                    self.file_path,
                    self.output_dir,
                    progress_callback=self.progress.emit,
                    enforce_min_length=self.enforce_min_length,
                    device=self.device,
                    progress_update=progress_update,
                    lang_code=self.lang_code,
                    voice=self.voice
                )
            elif ext == '.pdf':
                reader = PdfReader(self.file_path)
                valid_pages = [p for p in (page.extract_text() for page in reader.pages) if p and len(p.strip()) >= 100]
                total = len(valid_pages)
                self.progress_max.emit(total if total > 0 else 1)
                def progress_update(current):
                    self.progress_value.emit(current)
                process_pdf(
                    self.file_path,
                    self.output_dir,
                    progress_callback=self.progress.emit,
                    enforce_min_length=self.enforce_min_length,
                    device=self.device,
                    progress_update=progress_update,
                    lang_code=self.lang_code,
                    voice=self.voice
                )
            else:
                raise Exception("Unsupported file type. Please use .epub, .txt, or .pdf.")
            if not self._is_stopped:
                self.finished.emit(f"Done! WAV files in: {self.output_dir}")
        except Exception as e:
            self.finished.emit(f"Stopped: {e}" if self._is_stopped else f"Error: {e}")

    def stop(self):
        self._is_stopped = True


class DropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("kokoro-epub")
        self.setAcceptDrops(True)
        self.resize(400, 350)
        layout = QVBoxLayout()

        self.label = QLabel("Drop an EPUB, TXT, or PDF file here to generate an audio book.")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # Minimum text length checkbox
        self.min_length_checkbox = QCheckBox(f"Require Minimum Text Length ({MIN_TEXT_LENGTH} chars)")
        self.min_length_checkbox.setChecked(False)
        layout.addWidget(self.min_length_checkbox)

        # Language selection
        self.lang_label = QLabel("Select Language:")
        layout.addWidget(self.lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", ("a", "af_heart"))  # (lang_code, voice)
        self.lang_combo.addItem("Spanish", ("e", "ef_dora"))
        layout.addWidget(self.lang_combo)

        # Device selection
        self.device_label = QLabel("Select Processing Device:")
        layout.addWidget(self.device_label)

        self.device_combo = QComboBox()
        self.device_combo.addItem("Auto")
        self.device_combo.addItem("CUDA (GPU)")
        self.device_combo.addItem("CPU")
        layout.addWidget(self.device_combo)

        # Bitrate selection
        self.bitrate_label = QLabel("Select Output Bitrate:")
        layout.addWidget(self.bitrate_label)

        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItem("High Quality (128k)")
        self.bitrate_combo.addItem("Small Size (64k)")
        self.bitrate_combo.setCurrentIndex(1)
        layout.addWidget(self.bitrate_combo)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Buttons
        self.open_btn = QPushButton("Open Output Folder")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.open_output)
        layout.addWidget(self.open_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_processing)
        layout.addWidget(self.stop_btn)

        self.new_btn = QPushButton("New eBook")
        self.new_btn.setEnabled(False)
        self.new_btn.setVisible(False)
        self.new_btn.clicked.connect(self.reset_ui)
        layout.addWidget(self.new_btn)

        self.setLayout(layout)
        self.output_dir = "output"
        self.worker = None
        self.file_path = None  # CHANGED: keep dropped file path for naming

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        file_path = event.mimeData().urls()[0].toLocalFile()
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.epub', '.txt', '.pdf']:
            self.file_path = file_path  # CHANGED: store for later use
            self.label.setText("Processing...")
            self.open_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)

            enforce_min_length = self.min_length_checkbox.isChecked()
            device_choice = self.device_combo.currentText()
            if device_choice == "CUDA (GPU)":
                device = "cuda"
            elif device_choice == "CPU":
                device = "cpu"
            else:
                device = None  # Auto

            lang_code, voice = self.lang_combo.currentData()

            self.worker = Worker(
                file_path,
                self.output_dir,
                enforce_min_length,
                device,
                lang_code,
                voice
            )
            self.worker.progress.connect(self.label.setText)
            self.worker.finished.connect(self.done)
            self.worker.progress_value.connect(self.progress_bar.setValue)
            self.worker.progress_max.connect(self.progress_bar.setMaximum)
            self.worker.start()
        else:
            self.label.setText("Please drop a valid EPUB, TXT, or PDF file.")

    def done(self, msg):
        self.label.setText(msg)
        self.open_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        # Automatically merge audio files
        self.label.setText("Merging audio files...")
        def merge_progress_callback(m):
            self.label.setText(m)
            QApplication.processEvents()

        selected_bitrate = "128k" if self.bitrate_combo.currentIndex() == 0 else "64k"

        # CHANGED: name MP3 after the dropped file (epub/txt/pdf base name)
        base_name = os.path.splitext(os.path.basename(self.file_path or "audiobook"))[0]
        output_mp3 = os.path.join(self.output_dir, f"{base_name}.mp3")

        success = merge_audio_files(
            folder=self.output_dir,
            output_path=output_mp3,  # CHANGED
            progress_callback=merge_progress_callback,
            bitrate=selected_bitrate
        )

        if success:
            wav_files = glob.glob(os.path.join(self.output_dir, '*.wav'))
            for wav_file in wav_files:
                try:
                    os.remove(wav_file)
                except Exception as e:
                    print(f"Failed to delete {wav_file}: {e}")
            self.label.setText(f"Merge complete! WAV files deleted. See {os.path.basename(output_mp3)} in output folder.")
            self.new_btn.setEnabled(True)
            self.new_btn.setVisible(True)
        else:
            self.label.setText("No WAV files found to merge.")
            self.new_btn.setEnabled(True)
            self.new_btn.setVisible(True)

        self.worker = None  # moved after we used it

    def open_output(self):
        QFileDialog.getOpenFileName(self, "Open Output Folder", self.output_dir)

    def stop_processing(self):
        if self.worker is not None:
            self.worker.stop()
            self.label.setText("Stopping...")
            self.stop_btn.setEnabled(False)

    def reset_ui(self):
        self.label.setText("Drop an EPUB, TXT, or PDF file here to generate WAV files.")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.open_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.new_btn.setEnabled(False)
        self.new_btn.setVisible(False)
        self.worker = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DropWidget()
    window.show()
    sys.exit(app.exec())
