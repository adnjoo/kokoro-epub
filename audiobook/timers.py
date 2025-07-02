# timers.py

import time

class Timer:
    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def elapsed(self):
        if self.start_time is None:
            return 0
        return time.time() - self.start_time

    def print_elapsed(self, label=""):
        elapsed = self.elapsed()
        print(f"⏱️ {label} took {elapsed:.2f} seconds ({elapsed / 60:.2f} minutes)")

def estimate_total(chapters, avg_seconds_per_chapter=15):
    count = len(chapters)
    est_total = count * avg_seconds_per_chapter
    print(f"📖 Chapters to process: {count}")
    print(f"⏳ Estimated total time: {est_total:.2f} seconds ({est_total / 60:.2f} minutes)")
    return count
