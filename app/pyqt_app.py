import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
# Import the refactored process_epub function
from script import process_epub

class Worker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, epub_path, output_dir):
        super().__init__()
        self.epub_path = epub_path
        self.output_dir = output_dir

    def run(self):
        self.progress.emit(f"Processing: {os.path.basename(self.epub_path)}")
        try:
            process_epub(
                self.epub_path,
                self.output_dir,
                progress_callback=self.progress.emit
            )
            self.finished.emit(f"Done! WAV files in: {self.output_dir}")
        except Exception as e:
            self.finished.emit(f"Error: {e}")

class DropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPUB to Audio (Kokoro TTS)")
        self.setAcceptDrops(True)
        self.resize(400, 200)
        layout = QVBoxLayout()
        self.label = QLabel("Drop an EPUB file here to generate WAV files.")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.open_btn = QPushButton("Open Output Folder")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.open_output)
        layout.addWidget(self.open_btn)
        self.setLayout(layout)
        self.output_dir = "output"

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        epub_path = event.mimeData().urls()[0].toLocalFile()
        if epub_path.lower().endswith('.epub'):
            self.label.setText("Processing...")
            self.open_btn.setEnabled(False)
            self.worker = Worker(epub_path, self.output_dir)
            self.worker.progress.connect(self.label.setText)
            self.worker.finished.connect(self.done)
            self.worker.start()
        else:
            self.label.setText("Please drop a valid EPUB file.")

    def done(self, msg):
        self.label.setText(msg)
        self.open_btn.setEnabled(True)

    def open_output(self):
        QFileDialog.getOpenFileName(self, "Open Output Folder", self.output_dir)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DropWidget()
    window.show()
    sys.exit(app.exec_())