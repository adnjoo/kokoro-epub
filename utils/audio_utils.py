import os, shutil, subprocess
from pathlib import Path
from pydub import AudioSegment

def merge_to_mp3(wav_paths, out_mp3_path, bitrate="64k"):
    """Merge WAVs into a single MP3 using pydub/ffmpeg."""
    if shutil.which("ffmpeg") is None:
        return False
    combined = AudioSegment.silent(duration=0)
    for w in wav_paths:
        combined += AudioSegment.from_wav(w)
    combined.export(out_mp3_path, format="mp3", bitrate=bitrate)
    return True

def merge_to_m4b(wav_paths, out_m4b_path, chapters_txt=None, bitrate="64k"):
    """Merge WAVs into .m4b (AAC) with optional chapters metadata."""
    if shutil.which("ffmpeg") is None:
        return False
    list_file = Path(out_m4b_path).with_suffix(".concat.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for w in wav_paths:
            f.write(f"file '{Path(w).as_posix()}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file)]
    if chapters_txt:
        cmd += ["-i", str(chapters_txt), "-map_metadata", "1"]
    cmd += ["-c:a", "aac", "-b:a", bitrate, "-movflags", "faststart", str(out_m4b_path)]
    try:
        result = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False

def chapter_duration_ms(wav_files):
    """Return total duration in ms for a list of wavs."""
    return sum(len(AudioSegment.from_wav(w)) for w in wav_files)
