import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
# Import the refactored process_epub function
from script import process_epub
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup

class Worker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    progress_value = pyqtSignal(int)
    progress_max = pyqtSignal(int)

    def __init__(self, epub_path, output_dir):
        super().__init__()
        self.epub_path = epub_path
        self.output_dir = output_dir
        self._is_stopped = False

    def run(self):
        self.progress.emit(f"Processing: {os.path.basename(self.epub_path)}")
        try:
            # Estimate number of chapters for progress bar
            book = epub.read_epub(self.epub_path)
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
                self.epub_path,
                self.output_dir,
                progress_callback=progress_callback
            )
            if not self._is_stopped:
                self.finished.emit(f"Done! WAV files in: {self.output_dir}")
        except Exception as e:
            self.finished.emit(f"Stopped: {e}" if self._is_stopped else f"Error: {e}")

    def stop(self):
        self._is_stopped = True

class DropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPUB to Audio (Kokoro TTS)")
        self.setAcceptDrops(True)
        self.resize(400, 250)
        layout = QVBoxLayout()
        self.label = QLabel("Drop an EPUB file here to generate WAV files.")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
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
        self.setLayout(layout)
        self.output_dir = "output"
        self.worker = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        epub_path = event.mimeData().urls()[0].toLocalFile()
        if epub_path.lower().endswith('.epub'):
            self.label.setText("Processing...")
            self.open_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.worker = Worker(epub_path, self.output_dir)
            self.worker.progress.connect(self.label.setText)
            self.worker.finished.connect(self.done)
            self.worker.progress_value.connect(self.progress_bar.setValue)
            self.worker.progress_max.connect(self.progress_bar.setMaximum)
            self.worker.start()
        else:
            self.label.setText("Please drop a valid EPUB file.")

    def done(self, msg):
        self.label.setText(msg)
        self.open_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.worker = None

    def open_output(self):
        QFileDialog.getOpenFileName(self, "Open Output Folder", self.output_dir)

    def stop_processing(self):
        if self.worker is not None:
            self.worker.stop()
            self.label.setText("Stopping...")
            self.stop_btn.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DropWidget()
    window.show()
    sys.exit(app.exec_())