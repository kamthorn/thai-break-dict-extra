#!/usr/bin/env python3
"""
scripts/validate.py
Validates the format, encoding, sorting, and hygiene of dictionary files.
Can be used in CI / GitHub Actions or pre-commit hooks.
"""

import sys
from pathlib import Path
from collections import defaultdict

INVISIBLE_CHARS = {
    "\ufeff": "BOM (Byte Order Mark)",
    "\u200b": "Zero Width Space",
    "\u200c": "Zero Width Non-Joiner",
    "\u200d": "Zero Width Joiner",
    "\u200e": "Left-to-Right Mark",
    "\u200f": "Right-to-Left Mark",
    "\u00a0": "Non-breaking space",
}


def validate_file(filepath: Path) -> list[str]:
    """
    Validates an individual dictionary file.
    Returns a list of error strings found.
    """
    errors = []
    
    # 1. Check raw bytes for BOM and CRLF
    try:
        raw_bytes = filepath.read_bytes()
    except Exception as e:
        return [f"Failed to read file: {e}"]

    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        errors.append("File contains UTF-8 BOM. Files must be UTF-8 without BOM.")

    if b"\r" in raw_bytes:
        errors.append("File contains Windows CRLF or CR line endings. Use Unix LF (\\n).")

    # 2. Check UTF-8 decoding
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        errors.append(f"Invalid UTF-8 encoding: {e}")
        return errors

    # Check ending newline
    if text and not text.endswith("\n"):
        errors.append("File must end with a single newline (\\n).")

    lines = text.split("\n")
    # If file ends with \n, split produces an empty string as last element
    if lines and lines[-1] == "":
        lines.pop()

    seen_words = set()
    prev_word = ""

    for idx, line in enumerate(lines, start=1):
        # Empty line check
        if not line:
            errors.append(f"Line {idx}: Blank line found. Remove empty lines.")
            continue

        # Skip comments
        if line.startswith("#"):
            continue

        # Whitespace check
        if line != line.strip():
            errors.append(f"Line {idx}: '{line}' contains leading or trailing whitespace.")

        # Invisible characters check
        for char, desc in INVISIBLE_CHARS.items():
            if char in line:
                errors.append(f"Line {idx}: '{line}' contains invisible character {desc} (U+{ord(char):04X}).")

        # Single bare character check (length 1)
        if len(line) == 1:
            errors.append(
                f"Line {idx}: '{line}' is a bare single character. Bare single consonants break tokenizers and are disallowed."
            )

        # Duplicate check within file
        if line in seen_words:
            errors.append(f"Line {idx}: Duplicate word '{line}' found.")
        seen_words.add(line)

        # Sorting check
        if prev_word and line < prev_word:
            errors.append(
                f"Line {idx}: Word '{line}' is out of order (comes after '{prev_word}'). Files must be sorted."
            )
        prev_word = line

    return errors


def main():
    root_dir = Path(__file__).resolve().parent.parent
    data_dir = root_dir / "data"

    if not data_dir.exists():
        print(f"Error: Data directory not found at {data_dir}", file=sys.stderr)
        sys.exit(1)

    txt_files = sorted(data_dir.rglob("*.txt"))
    if not txt_files:
        print("Warning: No .txt files found in data directory.")
        return

    print(f"Validating {len(txt_files)} file(s) in {data_dir}...")
    total_errors = 0
    all_words_map = defaultdict(list)

    for file_path in txt_files:
        rel_path = file_path.relative_to(root_dir)
        errors = validate_file(file_path)
        if errors:
            print(f"❌ {rel_path} ({len(errors)} error(s)):")
            for err in errors[:10]:
                print(f"   - {err}")
            if len(errors) > 10:
                print(f"   ... and {len(errors) - 10} more errors")
            total_errors += len(errors)
        else:
            print(f"✓  {rel_path}")

        # Collect words for cross-file duplicate analysis
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith("#"):
                        all_words_map[word].append(str(rel_path))
        except Exception:
            pass

    # Cross-file duplicate warnings
    cross_duplicates = {w: paths for w, paths in all_words_map.items() if len(paths) > 1}
    if cross_duplicates:
        print(f"\n⚠️  Cross-category duplicates found ({len(cross_duplicates)} word(s)):")
        for word, paths in sorted(cross_duplicates.items())[:15]:
            print(f"   - '{word}' appears in: {', '.join(paths)}")
        if len(cross_duplicates) > 15:
            print(f"   ... and {len(cross_duplicates) - 15} more words in multiple files")

    print("\n" + "=" * 50)
    if total_errors == 0:
        print(f"✅ All {len(txt_files)} files passed validation!")
        sys.exit(0)
    else:
        print(f"❌ Validation failed with {total_errors} error(s). Run `python3 scripts/format.py` to auto-fix.")
        sys.exit(1)


if __name__ == "__main__":
    main()
