import os
import sys
import glob
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from processor import process_epub, process_txt, process_pdf
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from merge_audio import merge_audio_files

class WorkerThread(threading.Thread):
    def __init__(self, file_path, output_dir, progress_queue, stop_event):
        super().__init__()
        self.file_path = file_path
        self.output_dir = output_dir
        self.progress_queue = progress_queue
        self.stop_event = stop_event

    def run(self):
        ext = os.path.splitext(self.file_path)[1].lower()
        self.progress_queue.put(("progress", f"Processing: {os.path.basename(self.file_path)}"))
        try:
            if ext == ".epub":
                book = epub.read_epub(self.file_path)
                chapters = [item for item in book.items if item.get_type() == ITEM_DOCUMENT]
                total = sum(
                    1
                    for chapter in chapters
                    if len(BeautifulSoup(chapter.get_content(), "html.parser").get_text().strip()) >= 100
                )
                self.progress_queue.put(("max", total if total > 0 else 1))
                current = 0

                def progress_callback(msg):
                    self.progress_queue.put(("progress", msg))
                    if "Done chapter" in msg or "Done!" in msg:
                        nonlocal current
                        current += 1
                        self.progress_queue.put(("value", current))
                    if self.stop_event.is_set():
                        raise Exception("Processing stopped by user.")

                process_epub(self.file_path, self.output_dir, progress_callback=progress_callback)

            elif ext == ".txt":
                with open(self.file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) >= 100]
                self.progress_queue.put(("max", len(paragraphs) if paragraphs else 1))
                current = 0

                def progress_callback(msg):
                    self.progress_queue.put(("progress", msg))
                    if "Done chunk" in msg or "Done!" in msg:
                        nonlocal current
                        current += 1
                        self.progress_queue.put(("value", current))
                    if self.stop_event.is_set():
                        raise Exception("Processing stopped by user.")

                process_txt(self.file_path, self.output_dir, progress_callback=progress_callback)

            elif ext == ".pdf":
                from PyPDF2 import PdfReader

                reader = PdfReader(self.file_path)
                valid_pages = [
                    p for p in (page.extract_text() for page in reader.pages) if p and len(p.strip()) >= 100
                ]
                self.progress_queue.put(("max", len(valid_pages) if valid_pages else 1))
                current = 0

                def progress_callback(msg):
                    self.progress_queue.put(("progress", msg))
                    if "Done page" in msg or "Done!" in msg:
                        nonlocal current
                        current += 1
                        self.progress_queue.put(("value", current))
                    if self.stop_event.is_set():
                        raise Exception("Processing stopped by user.")

                process_pdf(self.file_path, self.output_dir, progress_callback=progress_callback)

            else:
                raise Exception("Unsupported file type. Please use .epub, .txt, or .pdf.")

            if not self.stop_event.is_set():
                self.progress_queue.put(("finished", f"Done! WAV files in: {self.output_dir}"))
        except Exception as e:
            if self.stop_event.is_set():
                self.progress_queue.put(("finished", f"Stopped: {e}"))
            else:
                self.progress_queue.put(("finished", f"Error: {e}"))

class VibeTailsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EPUB/TXT/PDF to Audio (Kokoro TTS)")
        self.geometry("450x250")
        self.resizable(False, False)

        self.output_dir = "output"
        self.worker = None
        self.stop_event = threading.Event()
        self.progress_queue = queue.Queue()

        # UI Elements
        self.label = ttk.Label(self, text="Select an EPUB, TXT, or PDF file to generate an audio book.", anchor="center")
        self.label.pack(pady=(20, 10), fill="x")

        self.progress_bar = ttk.Progressbar(self, length=400, mode="determinate")
        self.progress_bar.pack(pady=5)
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = 100
        self.progress_bar.pack_forget()

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        self.select_btn = ttk.Button(btn_frame, text="Select File", command=self.select_file)
        self.select_btn.grid(row=0, column=0, padx=5)

        self.open_btn = ttk.Button(btn_frame, text="Open Output Folder", command=self.open_output, state="disabled")
        self.open_btn.grid(row=0, column=1, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_processing, state="disabled")
        self.stop_btn.grid(row=0, column=2, padx=5)

        self.new_btn = ttk.Button(btn_frame, text="New eBook", command=self.reset_ui, state="disabled")
        self.new_btn.grid(row=0, column=3, padx=5)

        self.after(100, self.process_queue)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("eBook files", "*.epub *.txt *.pdf")], title="Select EPUB, TXT or PDF file"
        )
        if not file_path:
            return
        self.start_processing(file_path)

    def start_processing(self, file_path):
        self.label.config(text="Processing...")
        self.open_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.new_btn.config(state="disabled")
        self.progress_bar.pack()
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = 1

        self.stop_event.clear()
        self.worker = WorkerThread(file_path, self.output_dir, self.progress_queue, self.stop_event)
        self.worker.start()

    def process_queue(self):
        try:
            while True:
                msg_type, msg = self.progress_queue.get_nowait()
                if msg_type == "progress":
                    self.label.config(text=msg)
                elif msg_type == "value":
                    self.progress_bar["value"] = msg
                elif msg_type == "max":
                    self.progress_bar["maximum"] = msg
                elif msg_type == "finished":
                    self.done(msg)
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def done(self, msg):
        self.label.config(text=msg)
        self.open_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.progress_bar.pack_forget()
        self.worker = None

        # Merge audio files after processing
        self.label.config(text="Merging audio files...")
        self.update_idletasks()

        def merge_progress_callback(m):
            self.label.config(text=m)
            self.update_idletasks()

        success = merge_audio_files(
            folder=self.output_dir,
            output_path=os.path.join(self.output_dir, "full_book.mp3"),
            progress_callback=merge_progress_callback,
        )

        if success:
            # Delete all .wav files in the output directory
            wav_files = glob.glob(os.path.join(self.output_dir, "*.wav"))
            for wav_file in wav_files:
                try:
                    os.remove(wav_file)
                except Exception as e:
                    print(f"Failed to delete {wav_file}: {e}")
            self.label.config("Merge complete! WAV files deleted. See full_book.mp3 in output folder.")
            self.new_btn.config(state="normal")
        else:
            self.label.config("No WAV files found to merge.")
            self.new_btn.config(state="normal")

    def open_output(self):
        path = os.path.abspath(self.output_dir)
        if sys.platform == "darwin":
            os.system(f"open '{path}'")
        elif sys.platform == "win32":
            os.startfile(path)
        else:
            os.system(f"xdg-open '{path}'")

    def stop_processing(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self.label.config(text="Stopping...")
            self.stop_btn.config(state="disabled")

    def reset_ui(self):
        self.label.config(text="Select an EPUB, TXT, or PDF file to generate an audio book.")
        self.progress_bar.pack_forget()
        self.open_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.new_btn.config(state="disabled")
        self.worker = None

if __name__ == "__main__":
    app = VibeTailsApp()
    app.mainloop()
