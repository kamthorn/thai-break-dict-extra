#!/usr/bin/env python3
"""
scripts/format.py
Automatically cleans, deduplicates, and sorts word files in data/ in-place.
"""

import os
import sys
from pathlib import Path

# Characters to strip from words (e.g. invisible zero-width spaces, BOM)
STRIP_CHARS = "\ufeff\u200b\u200c\u200d\u200e\u200f\r\n\t "

def clean_and_format_file(filepath: Path) -> tuple[int, int]:
    """
    Cleans, deduplicates, and sorts words in a given file.
    Returns (original_count, formatted_count).
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    original_count = len(lines)
    unique_words = set()

    for line in lines:
        cleaned = line.strip(STRIP_CHARS)
        # Skip empty lines or comment lines
        if not cleaned or cleaned.startswith("#"):
            continue
        unique_words.add(cleaned)

    # Sort by unicode codepoint for consistency
    sorted_words = sorted(unique_words)

    # Write back in clean UTF-8 with standard \n
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        for word in sorted_words:
            f.write(f"{word}\n")

    return original_count, len(sorted_words)


def main():
    root_dir = Path(__file__).resolve().parent.parent
    data_dir = root_dir / "data"

    if not data_dir.exists():
        print(f"Error: Data directory not found at {data_dir}", file=sys.stderr)
        sys.exit(1)

    txt_files = sorted(data_dir.rglob("*.txt"))
    if not txt_files:
        print("No .txt files found in data directory.")
        return

    print(f"Formatting {len(txt_files)} file(s) in {data_dir}...")
    total_before = 0
    total_after = 0

    for file_path in txt_files:
        rel_path = file_path.relative_to(root_dir)
        before, after = clean_and_format_file(file_path)
        total_before += before
        total_after += after
        print(f"  ✓ {rel_path}: {after} words (was {before} lines)")

    print(f"\nDone! Total words formatted: {total_after} across {len(txt_files)} files.")


if __name__ == "__main__":
    main()
