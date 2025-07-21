import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QProgressBar, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6 import QtCore
# Import the refactored process_epub function
from processor import process_epub, process_txt, process_pdf, MIN_TEXT_LENGTH
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from merge_audio import merge_audio_files
import glob

class Worker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    progress_value = pyqtSignal(int)
    progress_max = pyqtSignal(int)

    def __init__(self, file_path, output_dir, enforce_min_length=True, device=None):
        super().__init__()
        self.file_path = file_path
        self.output_dir = output_dir
        self._is_stopped = False
        self.enforce_min_length = enforce_min_length
        self.device = device  # New

    def run(self):
        ext = os.path.splitext(self.file_path)[1].lower()
        self.progress.emit(f"Processing: {os.path.basename(self.file_path)}")
        try:
            if ext == '.epub':
                book = epub.read_epub(self.file_path)
                chapters = [item for item in book.items if item.get_type() == ITEM_DOCUMENT]
                total = sum(
                    1 for i, chapter in enumerate(chapters)
                    if len(BeautifulSoup(chapter.get_content(), 'html.parser').get_text().strip()) >= 100
                )
                self.progress_max.emit(total if total > 0 else 1)
                self._current = 0

                def progress_callback(msg):
                    self.progress.emit(msg)
                    if "Done chapter" in msg or "Done!" in msg:
                        self._current += 1
                        self.progress_value.emit(self._current)
                    if self._is_stopped:
                        raise Exception("Processing stopped by user.")

                process_epub(
                    self.file_path,
                    self.output_dir,
                    progress_callback=progress_callback,
                    enforce_min_length=self.enforce_min_length,
                    device=self.device
                )
            elif ext == '.txt':
                # Count paragraphs for progress bar
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) >= 100]
                self.progress_max.emit(len(paragraphs) if paragraphs else 1)
                self._current = 0
                def progress_callback(msg):
                    self.progress.emit(msg)
                    if "Done chunk" in msg or "Done!" in msg:
                        self._current += 1
                        self.progress_value.emit(self._current)
                    if self._is_stopped:
                        raise Exception("Processing stopped by user.")
                process_txt(
                    self.file_path,
                    self.output_dir,
                    progress_callback=progress_callback,
                    enforce_min_length=self.enforce_min_length,
                    device=self.device
                )
            elif ext == '.pdf':
                # Count valid pages for progress bar
                from PyPDF2 import PdfReader
                reader = PdfReader(self.file_path)
                valid_pages = [p for p in (page.extract_text() for page in reader.pages) if p and len(p.strip()) >= 100]
                self.progress_max.emit(len(valid_pages) if valid_pages else 1)
                self._current = 0
                def progress_callback(msg):
                    self.progress.emit(msg)
                    if "Done page" in msg or "Done!" in msg:
                        self._current += 1
                        self.progress_value.emit(self._current)
                    if self._is_stopped:
                        raise Exception("Processing stopped by user.")
                process_pdf(
                    self.file_path,
                    self.output_dir,
                    progress_callback=progress_callback,
                    enforce_min_length=self.enforce_min_length,
                    device=self.device
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
        self.setWindowTitle("EPUB/TXT/PDF to Audio (Kokoro TTS)")
        self.setAcceptDrops(True)
        self.resize(400, 250)
        layout = QVBoxLayout()
        self.label = QLabel("Drop an EPUB, TXT, or PDF file here to generate an audio book.")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        # Add checkbox for minimum text length enforcement
        self.min_length_checkbox = QCheckBox(f"Enforce Minimum Text Length ({MIN_TEXT_LENGTH} chars)")
        self.min_length_checkbox.setChecked(True)
        layout.addWidget(self.min_length_checkbox)
        self.device_combo = QComboBox()
        self.device_combo.addItem("Auto")  # Let code decide (default)
        self.device_combo.addItem("CUDA (GPU)")
        self.device_combo.addItem("CPU")
        layout.addWidget(self.device_combo)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
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

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        file_path = event.mimeData().urls()[0].toLocalFile()
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.epub', '.txt', '.pdf']:
            self.label.setText("Processing...")
            self.open_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            # Pass checkbox state to Worker (to be wired to processing logic)
            enforce_min_length = self.min_length_checkbox.isChecked()
            device_choice = self.device_combo.currentText()
            if device_choice == "CUDA (GPU)":
                device = "cuda"
            elif device_choice == "CPU":
                device = "cpu"
            else:
                device = None  # Auto
            self.worker = Worker(file_path, self.output_dir, enforce_min_length, device)
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
        self.worker = None

        # Automatically merge audio files after TTS is done
        self.label.setText("Merging audio files...")
        def merge_progress_callback(m):
            self.label.setText(m)
            QApplication.processEvents()
        success = merge_audio_files(
            folder=self.output_dir,
            output_path=os.path.join(self.output_dir, "full_book.mp3"),
            progress_callback=merge_progress_callback
        )
        if success:
            # Delete all .wav files in the output directory
            wav_files = glob.glob(os.path.join(self.output_dir, '*.wav'))
            for wav_file in wav_files:
                try:
                    os.remove(wav_file)
                except Exception as e:
                    print(f"Failed to delete {wav_file}: {e}")
            self.label.setText("Merge complete! WAV files deleted. See full_book.mp3 in output folder.")
            self.new_btn.setEnabled(True)
            self.new_btn.setVisible(True)
        else:
            self.label.setText("No WAV files found to merge.")
            self.new_btn.setEnabled(True)
            self.new_btn.setVisible(True)

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