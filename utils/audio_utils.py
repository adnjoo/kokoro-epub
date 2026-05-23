import os, shutil, subprocess
import tempfile
from pathlib import Path
from pydub import AudioSegment


def merge_to_mp3(wav_paths, out_mp3_path, bitrate="64k"):
    """
    Merges multiple WAV files into a single MP3 using FFmpeg's concat demuxer.
    This bypasses pydub/wave 4GB size limits and uses significantly less memory.
    """
    if shutil.which("ffmpeg") is None:
        print("Warning: FFmpeg is not installed or not in PATH.")
        return False

    try:
        # Create a temporary text file listing all the WAVs for FFmpeg
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            for wav in wav_paths:
                # FFmpeg requires forward slashes even on Windows
                safe_path = str(Path(wav).resolve()).replace('\\', '/')
                f.write(f"file '{safe_path}'\n")
            list_file_path = f.name

        # Run FFmpeg to concatenate directly
        command = [
            "ffmpeg",
            "-y",  # Overwrite output if it exists
            "-f", "concat",  # Use the concat demuxer
            "-safe", "0",  # Allow absolute paths in the text file
            "-i", list_file_path,
            "-c:a", "libmp3lame",
            "-b:a", bitrate,
            str(out_mp3_path)
        ]

        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Clean up the temp list file
        Path(list_file_path).unlink(missing_ok=True)
        return True

    except Exception as e:
        print(f"Error merging MP3 with FFmpeg directly: {e}")
        return False


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