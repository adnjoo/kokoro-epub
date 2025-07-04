# merge_audio.py

from pydub import AudioSegment
import os
import re

def natural_key(filename):
    """Sorts like: chapter_01_2.wav < chapter_01_10.wav"""
    numbers = re.findall(r'\d+', filename)
    return list(map(int, numbers))  # e.g., [1, 2] from 'chapter_01_2.wav'

def merge_audio_files(folder="output", output_path=None, progress_callback=None):
    if output_path is None:
        output_path = os.path.join(folder, "full_book.mp3")
    # Get sorted .wav files
    wav_files = sorted(
        [f for f in os.listdir(folder) if f.endswith(".wav")],
        key=natural_key
    )
    if not wav_files:
        msg = "No WAV files found in output folder."
        if progress_callback:
            progress_callback(msg)
        else:
            print(msg)
        return False
    # Stitch together
    combined = AudioSegment.empty()
    for idx, f in enumerate(wav_files):
        path = os.path.join(folder, f)
        msg = f"Adding {path} ({idx+1}/{len(wav_files)})..."
        if progress_callback:
            progress_callback(msg)
        else:
            print(msg)
        audio = AudioSegment.from_wav(path)
        combined += audio
    msg = f"\n✅ Combined audiobook saved to: {output_path}"
    combined.export(output_path, format="mp3", bitrate="128k")
    if progress_callback:
        progress_callback(msg)
    else:
        print(msg)
    return True

if __name__ == "__main__":
    merge_audio_files()
