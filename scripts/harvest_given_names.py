#!/usr/bin/env python3
"""
scripts/harvest_given_names.py
Harvests Thai given names (person_names_female_th.txt / person_names_male_th.txt,
CC0/Apache-2.0, from PyThaiNLP) -> data/proper-names/given-names.txt

Why: many two-syllable Thai given names are composed of two morphemes that are
*both* already real dictionary words (e.g. สมศักดิ์ = สม + ศักดิ์), so a
segmenter correctly-by-the-rules but wrongly-in-meaning splits them
(สมศักดิ์ -> สม|ศักดิ์), since a single dictionary word always beats a
two-word decomposition once the whole name is itself listed.

A name is skipped when its surface form also occurs as an ordinary two-word
sequence *outside* any person-name (PER) span in the LST20 gold-segmented
corpus at least --min-risk times (default 2) — meaning it is also common
vocabulary (e.g. โชคดี "lucky", สายพันธุ์ "strain/breed"), and merging it
unconditionally would wrongly glue together ordinary sentences that happen
to contain it. Per corpora.py's policy, LST20 is used only to decide which
words to add; no LST20 text is written into data/ or dist/.

Usage:
  python3 scripts/harvest_given_names.py [--lst20 ../LST20_Corpus]

Validated on the LST20 test split (held out from selection) merged into
thai-break's own dictionary: boundary-level word-segmentation F1 94.03% ->
94.21% (net +814 correct boundaries across 483 documents, 883 fixed vs.
69 newly wrong). Re-run scripts/evaluate_lst20.py after harvesting to
reproduce.
"""

import argparse
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUT_PATH = DATA_DIR / "proper-names" / "given-names.txt"

FEMALE_URL = "https://raw.githubusercontent.com/PyThaiNLP/pythainlp/dev/pythainlp/corpus/person_names_female_th.txt"
MALE_URL = "https://raw.githubusercontent.com/PyThaiNLP/pythainlp/dev/pythainlp/corpus/person_names_male_th.txt"


def fetch_names(url: str) -> set[str]:
    with urllib.request.urlopen(url, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    return {line.strip() for line in text.splitlines() if line.strip()}


def load_words_file(path: Path) -> set[str]:
    words = set()
    if not path.exists():
        return words
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                words.add(line.split("\t", 1)[0])
    return words


def ordinary_bigrams(lst20_dir: Path) -> Counter:
    """Counter of 'word1word2' (concatenated) for consecutive gold tokens in
    LST20 train+eval that do NOT both fall inside the same named-entity span
    (so the count reflects ordinary running text, not name-internal structure).
    Reads the NE column directly since corpora.lst20_file_chunks() discards it."""
    bigrams = Counter()
    files = []
    for split in ("train", "eval"):
        d = lst20_dir / split
        if d.exists():
            files += [p for p in sorted(d.glob("*.txt")) if not p.name.startswith("._")]
    for path in files:
        prev_word, prev_ne = None, None
        with open(path, encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                line = raw.rstrip("\n")
                if not line:
                    prev_word, prev_ne = None, None
                    continue
                parts = line.split("\t")
                if len(parts) < 3:
                    prev_word, prev_ne = None, None
                    continue
                word, ne = parts[0], parts[2]
                if word == "_" or not word:
                    prev_word, prev_ne = None, None
                    continue
                if prev_word is not None:
                    same_entity = (
                        ne.startswith("I_") and prev_ne is not None
                        and prev_ne[2:] == ne[2:]
                        and (prev_ne.startswith("B_") or prev_ne.startswith("I_"))
                    )
                    if not same_entity:
                        bigrams[prev_word + word] += 1
                prev_word, prev_ne = word, ne
    return bigrams


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lst20", type=Path, default=Path("../LST20_Corpus"),
                     help="path to the LST20_Corpus directory (train/eval subdirs; default: ../LST20_Corpus)")
    ap.add_argument("--min-risk", type=int, default=2,
                     help="exclude a name occurring as an ordinary (non-PER) bigram at least this many times (default: 2)")
    ap.add_argument("--base-dict", type=Path, default=Path("../thai-break/data/words.txt"),
                     help="existing base dictionary to skip names already present")
    args = ap.parse_args()

    if not args.lst20.exists():
        print(f"Error: LST20 directory not found at {args.lst20} (pass --lst20)", file=sys.stderr)
        sys.exit(1)

    print("Fetching PyThaiNLP name lists...", file=sys.stderr)
    names = fetch_names(FEMALE_URL) | fetch_names(MALE_URL)
    print(f"{len(names)} unique names from PyThaiNLP (female+male)", file=sys.stderr)

    existing = load_words_file(args.base_dict) | load_words_file(OUT_PATH)
    names -= existing
    print(f"{len(names)} candidates after removing existing dictionary entries", file=sys.stderr)

    bigrams = ordinary_bigrams(args.lst20)
    print(f"{len(bigrams):,} ordinary (non-PER) bigrams found in LST20 train+eval", file=sys.stderr)

    risky = sorted((n for n in names if bigrams.get(n, 0) >= args.min_risk), key=lambda n: -bigrams[n])
    safe = sorted(n for n in names if bigrams.get(n, 0) < args.min_risk)
    print(f"Excluded (collide with ordinary phrases): {len(risky)}", file=sys.stderr)
    for n in risky[:25]:
        print(f"  {n:<12} used as an ordinary phrase {bigrams[n]}x", file=sys.stderr)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing_out = load_words_file(OUT_PATH)
    merged = sorted(existing_out | set(safe))
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for n in merged:
            f.write(n + "\n")
    print(f"✓ Given names: wrote {len(merged)} total ({len(safe)} newly added) to "
          f"{OUT_PATH.relative_to(ROOT_DIR)}", file=sys.stderr)


if __name__ == "__main__":
    main()
