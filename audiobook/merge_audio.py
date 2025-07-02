from pydub import AudioSegment
import os
import re

folder = "audiobook"
output_path = os.path.join(folder, "full_book.mp3")

def natural_key(filename):
    """Sorts like: chapter_01_2.wav < chapter_01_10.wav"""
    numbers = re.findall(r'\d+', filename)
    return list(map(int, numbers))  # e.g., [1, 2] from 'chapter_01_2.wav'

# Get sorted .wav files
wav_files = sorted(
    [f for f in os.listdir(folder) if f.endswith(".wav")],
    key=natural_key
)

# Stitch together
combined = AudioSegment.empty()
for f in wav_files:
    path = os.path.join(folder, f)
    print(f"Adding {path}...")
    audio = AudioSegment.from_wav(path)
    combined += audio

# combined.export(output_path, format="wav") # large file size
combined.export("output/full_book.mp3", format="mp3", bitrate="128k")

print(f"\n✅ Combined audiobook saved to: {output_path}")
