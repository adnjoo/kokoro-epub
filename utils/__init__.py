# utils/__init__.py
"""
Utility package for kokoro-epub.

This exposes the most common helpers so they can be imported
directly from `utils` instead of deep submodules.
"""

from .audio_utils import merge_to_mp3, merge_to_m4b, chapter_duration_ms
from .metadata_utils import write_chapters_metadata
from .extract_chapters import extract_chapters

__all__ = [
    "merge_to_mp3",
    "merge_to_m4b",
    "chapter_duration_ms",
    "write_chapters_metadata",
    "extract_chapters",
]
