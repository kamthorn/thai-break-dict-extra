#!/usr/bin/env python3
"""
Harvest novel Thai vocabulary from Wisesight Sentiment corpus (CC0-1.0).

Strategy:
  1. Load Wisesight train + test text (public GitHub raw)
  2. Tokenize with newmm (PyThaiNLP) using its default dict
  3. Collect single Thai-only tokens (len 2–8) that appear ≥ MIN_FREQ times
  4. Filter against existing words in our dictionaries
  5. Also extract novel words from words_th_thai2fit_201810.txt (PyThaiNLP, CC0)
  6. Merge, deduplicate, categorize, and write new slang candidates

Output: data/slang/internet_new.txt  (for manual review before merging)
"""

import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
MIN_FREQ = 5
MIN_LEN = 2
MAX_LEN = 8
THAI_ONLY = re.compile(r"^[\u0E00-\u0E7F]{2,8}$")

WISESIGHT_URLS = [
    "https://raw.githubusercontent.com/PyThaiNLP/wisesight-sentiment/master/kaggle-competition/train.txt",
    "https://raw.githubusercontent.com/PyThaiNLP/wisesight-sentiment/master/kaggle-competition/test.txt",
]

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
SLANG_DIR = DATA_DIR / "slang"
EXISTING_SLANG = SLANG_DIR / "internet.txt"
OUTPUT = SLANG_DIR / "internet_new.txt"

# Words in our existing dictionaries (to filter out already-known words)
KNOWN_WORDS_FILES = [
    ROOT.parent / "thai-break" / "data" / "words.txt",
    ROOT / "dist" / "words-extra.txt",
]

# Thai2fit novel word list (PyThaiNLP corpus, CC0)
THAI2FIT_PATH = (
    Path("/home/kamthorn/code/pythainlp")
    / "pythainlp" / "corpus" / "words_th_thai2fit_201810.txt"
)


def load_known_words() -> set:
    known = set()
    for p in KNOWN_WORDS_FILES:
        if p.exists():
            with open(p, encoding="utf-8") as f:
                for line in f:
                    w = line.strip()
                    if w and not w.startswith("#"):
                        known.add(w)
    # Also load existing slang so we don't duplicate
    if EXISTING_SLANG.exists():
        with open(EXISTING_SLANG, encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w and not w.startswith("#"):
                    known.add(w)
    print(f"[info] Loaded {len(known):,} known words")
    return known


def fetch_wisesight_lines() -> list[str]:
    lines = []
    for url in WISESIGHT_URLS:
        print(f"[fetch] {url}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ThaiBreakHarvest/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = resp.read().decode("utf-8")
            chunk = text.splitlines()
            lines.extend(chunk)
            print(f"        → {len(chunk):,} lines")
        except Exception as e:
            print(f"[warn] Failed to fetch {url}: {e}", file=sys.stderr)
    return lines


def tokenize_with_newmm(lines: list[str]) -> Counter:
    """Tokenize using PyThaiNLP newmm if available, else fallback to nlpo3."""
    counter: Counter = Counter()

    try:
        from pythainlp.tokenize import word_tokenize
        engine = "newmm"
        print(f"[info] Using pythainlp {engine} tokenizer")
        for i, line in enumerate(lines):
            if i % 5000 == 0:
                print(f"  tokenizing line {i:,}/{len(lines):,} ...", end="\r")
            try:
                tokens = word_tokenize(line.strip(), engine=engine)
                for tok in tokens:
                    tok = tok.strip()
                    if THAI_ONLY.match(tok):
                        counter[tok] += 1
            except Exception:
                pass
        print()
    except ImportError:
        # Fallback: simple Thai character splitting by non-Thai boundaries
        print("[warn] pythainlp not available; using character-boundary fallback")
        non_thai = re.compile(r"[^\u0E00-\u0E7F]+")
        for line in lines:
            parts = non_thai.split(line)
            for part in parts:
                if THAI_ONLY.match(part):
                    counter[part] += 1

    return counter


def extract_thai2fit_novel(known: set) -> list[str]:
    """Return Thai2fit words not in our known set, Thai-only, len 2-12."""
    if not THAI2FIT_PATH.exists():
        print(f"[skip] Thai2fit file not found: {THAI2FIT_PATH}")
        return []
    print(f"[fetch] Thai2fit vocab: {THAI2FIT_PATH}")
    thai_pat = re.compile(r"^[\u0E00-\u0E7F]{2,12}$")
    novel = []
    with open(THAI2FIT_PATH, encoding="utf-8") as f:
        for line in f:
            w = line.strip()
            if w and thai_pat.match(w) and w not in known:
                novel.append(w)
    print(f"[info] Thai2fit novel words: {len(novel):,}")
    return novel


def main():
    print("=" * 60)
    print("Wisesight Vocabulary Harvester")
    print("=" * 60)

    known = load_known_words()

    # ── Wisesight extraction ──────────────────────────────────────────────────
    raw_lines = fetch_wisesight_lines()
    print(f"[info] Total Wisesight lines: {len(raw_lines):,}")

    token_counts = tokenize_with_newmm(raw_lines)
    print(f"[info] Unique Thai tokens: {len(token_counts):,}")

    # Filter
    candidates_wisesight = {
        w: c
        for w, c in token_counts.items()
        if c >= MIN_FREQ and w not in known and MIN_LEN <= len(w) <= MAX_LEN
    }
    sorted_wisesight = sorted(candidates_wisesight.items(), key=lambda x: -x[1])
    print(f"[info] Wisesight novel candidates (freq≥{MIN_FREQ}): {len(sorted_wisesight):,}")

    # ── Thai2fit extraction ───────────────────────────────────────────────────
    thai2fit_novel = extract_thai2fit_novel(known)

    # ── Write output ──────────────────────────────────────────────────────────
    SLANG_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("# Auto-harvested vocabulary candidates — REVIEW BEFORE MERGING\n")
        f.write("# Source: Wisesight Sentiment (CC0-1.0) + Thai2fit (CC0)\n")
        f.write("#\n")

        f.write("# === Wisesight candidates (freq ≥ {}) ===\n".format(MIN_FREQ))
        for w, c in sorted_wisesight:
            f.write(f"{w}  # freq={c}\n")

        f.write("\n# === Thai2fit novel words (sample, first 2000) ===\n")
        for w in thai2fit_novel[:2000]:
            f.write(f"{w}\n")

    print(f"\n[done] Written → {OUTPUT}")
    print(f"       Wisesight candidates : {len(sorted_wisesight):,}")
    print(f"       Thai2fit novel sample: {min(len(thai2fit_novel), 2000):,}")
    print(f"\nReview {OUTPUT} and merge selected entries into internet.txt")


if __name__ == "__main__":
    main()
