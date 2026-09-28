#!/usr/bin/env python3
"""
Curate and merge vocabulary from harvest output into our dictionaries.

Rules:
  - Wisesight: keep only SHORT (2-3 char) Thai-only tokens that are abbreviations
    or informal words; skip compound phrases (anything matching spaces/compound patterns)
  - Thai2fit: filter for standard Thai single-morpheme words (2-10 chars, no spaces)
    and add to data/general/ as a new general vocabulary category

Usage:
  python3 scripts/curate_harvest.py [--dry-run]
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

# Source
HARVEST_FILE = DATA_DIR / "slang" / "internet_new.txt"

# Destinations
SLANG_DEST = DATA_DIR / "slang" / "internet.txt"
GENERAL_DEST = DATA_DIR / "general" / "thai2fit.txt"  # new category

# Patterns
THAI_ONLY = re.compile(r"^[\u0E00-\u0E7F]+$")
# Compound: likely multi-word if it's long without clearly single morpheme
# These are "likely slang" patterns: short (2-4 chars), Thai-only, not in known dict
LIKELY_ABBREV = re.compile(r"^[\u0E00-\u0E7F]{2,4}$")

# Known good slang/abbreviation patterns to keep from Wisesight
WISESIGHT_KEEPLIST_PATTERNS = [
    # Very short = likely abbreviation or interjection
    re.compile(r"^[\u0E00-\u0E7F]{2,3}$"),
    # Onomatopoeia / laughter: อิอิ, ฮ่าๆ etc (handled by existing slang already)
]

# Thai2fit words to skip (patterns that suggest compound / phrase / non-standard)
THAI2FIT_SKIP = re.compile(
    r"(สูงสุด|แห่ง|บัญญัติ|กฎ|หมาย|บรรณ|ระเบียบ|ทาน|วินัย|ศีล|ธรรม)"
    r"|ๆ"  # repetition mark in middle of word = informal/compound
)

DRY_RUN = "--dry-run" in sys.argv


def load_existing(path: Path) -> set:
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        return {
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        }


def parse_harvest(path: Path):
    """Yield (word, section, freq) from internet_new.txt"""
    section = "wisesight"
    freq_pat = re.compile(r"freq=(\d+)")
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            # Check section markers BEFORE skipping comment lines
            if "Thai2fit" in line:
                section = "thai2fit"
            if not line or line.startswith("#"):
                continue
            word = line.split("  #")[0].strip()
            m = freq_pat.search(line)
            freq = int(m.group(1)) if m else 0
            yield word, section, freq


def main():
    if not HARVEST_FILE.exists():
        print(f"[error] Harvest file not found: {HARVEST_FILE}")
        print("Run harvest_wisesight_vocab.py first.")
        sys.exit(1)

    existing_slang = load_existing(SLANG_DEST)
    existing_general = load_existing(GENERAL_DEST)

    slang_new = []
    general_new = []

    for word, section, freq in parse_harvest(HARVEST_FILE):
        if not THAI_ONLY.match(word):
            continue

        if section == "wisesight":
            # Only keep very short words (likely abbreviations / interjections)
            if len(word) <= 3 and word not in existing_slang:
                slang_new.append((word, freq, "wisesight"))

        elif section == "thai2fit":
            # General vocab: 2-10 chars, not compound-looking, not already known
            if (
                2 <= len(word) <= 10
                and not THAI2FIT_SKIP.search(word)
                and word not in existing_general
            ):
                general_new.append(word)

    print(f"[info] New slang candidates: {len(slang_new)}")
    print(f"[info] New general vocab candidates: {len(general_new)}")

    if DRY_RUN:
        print("\n--- Slang candidates (dry-run) ---")
        for w, f, src in slang_new:
            print(f"  {w}  # freq={f} src={src}")
        print(f"\n--- General vocab candidates (first 30) ---")
        for w in general_new[:30]:
            print(f"  {w}")
        return

    # ── Write slang additions ──────────────────────────────────────────────────
    if slang_new:
        with open(SLANG_DEST, "a", encoding="utf-8") as f:
            f.write("\n# === Added from Wisesight Sentiment (CC0-1.0) ===\n")
            for w, freq, src in sorted(slang_new, key=lambda x: -x[1]):
                f.write(f"{w}\n")
        print(f"[done] Appended {len(slang_new)} words to {SLANG_DEST}")

    # ── Write general vocab ────────────────────────────────────────────────────
    if general_new:
        GENERAL_DEST.parent.mkdir(parents=True, exist_ok=True)
        with open(GENERAL_DEST, "w", encoding="utf-8") as f:
            f.write("# Thai2fit general vocabulary (CC0-1.0, from PyThaiNLP)\n")
            f.write("# Source: pythainlp/corpus/words_th_thai2fit_201810.txt\n")
            f.write("# Filtered: Thai-only, 2-10 chars, non-compound heuristic\n")
            f.write("#\n")
            for w in sorted(general_new):
                f.write(f"{w}\n")
        print(f"[done] Written {len(general_new)} words to {GENERAL_DEST}")


if __name__ == "__main__":
    main()
