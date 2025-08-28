def write_chapters_metadata(chapter_durations, out_txt):
    """
    chapter_durations: [(title, duration_ms), ...]
    """
    offset = 0
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(";FFMETADATA1\n")
        for title, dur in chapter_durations:
            start = offset
            end = offset + dur
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={start}\n")
            f.write(f"END={end}\n")
            f.write(f"title={title}\n\n")
            offset = end
