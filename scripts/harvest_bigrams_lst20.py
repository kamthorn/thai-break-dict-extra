#!/usr/bin/env python3
"""
Extract Thai bigrams from LST20 Corpus (gold-standard word segmentation).

The LST20 corpus has a USAGE AGREEMENT — we must NOT redistribute the corpus
or derived data containing raw text. Bigram counts are therefore written to
local/ (gitignored, never committed) for local experiments and runtime use
only. See README "IMPORTANT" note. Only bigrams extracted from CC0 / Apache-2.0
sources (e.g. Wisesight, Prachathai-67k) may be committed under data/.

Output format: word1\tword2\tcount
Threshold: Only bigrams with count >= MIN_COUNT are kept to reduce file size.

Usage:
  python3 scripts/harvest_bigrams_lst20.py [--lst20-dir /path/to/LST20_Corpus] [--min-count 3] [--output local/bigrams.tsv]
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

# Add scripts/ to path so we can import corpora.py
sys.path.insert(0, str(Path(__file__).parent))
from corpora import lst20_chunks

DEFAULT_LST20_DIR = Path("/home/kamthorn/code/LST20_Corpus")
DEFAULT_OUTPUT = Path(__file__).parent.parent / "local" / "bigrams.tsv"
DEFAULT_MIN_COUNT = 3


def extract_bigrams(lst20_dir: Path, min_count: int) -> Counter:
    """Extract word bigrams from LST20 gold segmentation (train + eval splits)."""
    bigrams: Counter = Counter()
    total_words = 0
    total_chunks = 0

    for split in ("eval",):  # use eval only — smaller but clean; train is huge
        split_dir = lst20_dir / split
        if not split_dir.exists():
            print(f"[warn] Split dir not found: {split_dir}", file=sys.stderr)
            continue

        print(f"[info] Processing {split_dir} ...")
        for chunk in lst20_chunks(split_dir):
            if len(chunk) < 2:
                continue
            total_chunks += 1
            total_words += len(chunk)
            for i in range(len(chunk) - 1):
                w1 = chunk[i].strip()
                w2 = chunk[i + 1].strip()
                if w1 and w2:
                    bigrams[(w1, w2)] += 1

    print(f"[info] Processed {total_chunks:,} chunks, {total_words:,} words")
    print(f"[info] Raw bigram types: {len(bigrams):,}")
    return bigrams


def main():
    parser = argparse.ArgumentParser(description="Extract bigrams from LST20 corpus")
    parser.add_argument("--lst20-dir", default=str(DEFAULT_LST20_DIR), help="Path to LST20 corpus root")
    parser.add_argument("--min-count", type=int, default=DEFAULT_MIN_COUNT, help="Minimum bigram count")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output TSV path")
    args = parser.parse_args()

    lst20_dir = Path(args.lst20_dir)
    if not lst20_dir.exists():
        print(f"[error] LST20 directory not found: {lst20_dir}")
        print("Please download the LST20 corpus and provide the path via --lst20-dir")
        sys.exit(1)

    output_path = Path(args.output)

    bigrams = extract_bigrams(lst20_dir, args.min_count)

    # Filter by min_count
    filtered = {(w1, w2): c for (w1, w2), c in bigrams.items() if c >= args.min_count}
    print(f"[info] Bigrams with count >= {args.min_count}: {len(filtered):,}")

    # Sort by count descending
    sorted_bigrams = sorted(filtered.items(), key=lambda x: -x[1])

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Thai word bigrams extracted from LST20 Corpus (gold segmentation)\n")
        f.write("# Format: word1<TAB>word2<TAB>count\n")
        f.write(f"# Minimum count: {args.min_count}\n")
        f.write(f"# Total bigram types: {len(sorted_bigrams):,}\n")
        f.write("#\n")
        for (w1, w2), count in sorted_bigrams:
            f.write(f"{w1}\t{w2}\t{count}\n")

    print(f"[done] Written {len(sorted_bigrams):,} bigrams → {output_path}")


if __name__ == "__main__":
    main()
