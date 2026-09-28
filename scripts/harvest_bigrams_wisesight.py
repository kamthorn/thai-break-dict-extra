#!/usr/bin/env python3
"""
scripts/harvest_bigrams_wisesight.py
Extract word bigrams from HUMAN-tokenized Wisesight samples (CC0-1.0).

Source: PyThaiNLP/wisesight-sentiment, word-tokenization/
  - wisesight-1000-samples-tokenised.label (993 sentences)
  - wisesight-160-samples-tokenised.label (160 sentences)
Tokens are `|`-separated by human annotators; bare-space tokens are dropped,
everything else (words, numbers, punctuation, emoji) is kept, matching how
BigramModel looks up tokenizer output pairs.

Why this instead of LST20 bigrams: the LST20 usage agreement forbids
redistributing any part of the dataset, so LST20-derived bigrams live in
local/ only. Wisesight is CC0-1.0 public domain, therefore safe to commit
under data/ and ship in releases. The corpus is small (~1.1k sentences),
so this file is a clean seed; extend with Prachathai-67k (Apache-2.0)
when volume matters.

Output: data/bigrams-wisesight.tsv  (word1<TAB>word2<TAB>count)
Raw downloads are cached in local/ (gitignored).

Usage:
  python3 scripts/harvest_bigrams_wisesight.py [--min-count 2]
"""

import argparse
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / "local"
OUTPUT = ROOT / "data" / "bigrams-wisesight.tsv"

SOURCES = {
    "wisesight-1000-samples-tokenised.label": (
        "https://raw.githubusercontent.com/PyThaiNLP/wisesight-sentiment"
        "/master/word-tokenization/wisesight-1000-samples-tokenised.label"
    ),
    "wisesight-160-samples-tokenised.label": (
        "https://raw.githubusercontent.com/PyThaiNLP/wisesight-sentiment"
        "/master/word-tokenization/wisesight-160-samples-tokenised.label"
    ),
}


def fetch(name: str, url: str) -> list[str]:
    cached = LOCAL / name
    if cached.exists():
        print(f"[cache] {cached}")
        return cached.read_text(encoding="utf-8").splitlines()
    print(f"[fetch] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "ThaiBreakHarvest/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            text = resp.read().decode("utf-8")
    except Exception as e:
        print(f"[error] download failed: {e}", file=sys.stderr)
        sys.exit(1)
    LOCAL.mkdir(parents=True, exist_ok=True)
    cached.write_text(text, encoding="utf-8")
    return text.splitlines()


def parse_label_line(line: str) -> list[str]:
    """Split a human-tokenized `|`-separated line, dropping bare spaces."""
    tokens = []
    for tok in line.split("|"):
        if tok.strip():
            tokens.append(tok.strip())
    return tokens


def main() -> None:
    ap = argparse.ArgumentParser(description="Harvest CC0 bigrams from Wisesight")
    ap.add_argument("--min-count", type=int, default=2)
    ap.add_argument("--output", type=Path, default=OUTPUT)
    args = ap.parse_args()

    bigrams: Counter = Counter()
    n_sent, n_tok = 0, 0
    for name, url in SOURCES.items():
        for line in fetch(name, url):
            toks = parse_label_line(line)
            if len(toks) < 2:
                continue
            n_sent += 1
            n_tok += len(toks)
            for i in range(len(toks) - 1):
                bigrams[(toks[i], toks[i + 1])] += 1

    print(f"[info] {n_sent:,} sentences, {n_tok:,} tokens, "
          f"{len(bigrams):,} raw bigram types")
    kept = {k: c for k, c in bigrams.items() if c >= args.min_count}
    # BigramModel loaders skip lines starting with '#', so hashtag-leading
    # pairs (w1 = '#...') would be silently dropped at load time — exclude
    # them here so the committed count is exactly what loads.
    dropped_hash = sum(1 for (w1, _w2) in kept if w1.startswith("#"))
    kept = {k: c for k, c in kept.items() if not k[0].startswith("#")}
    print(f"[info] bigrams with count >= {args.min_count}: {len(kept):,} "
          f"(excluded {dropped_hash} hashtag-leading rows unloadable by loaders)")

    out: Path = args.output
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Thai word bigrams from HUMAN-tokenized Wisesight samples (CC0-1.0)\n")
        f.write("# Source: PyThaiNLP/wisesight-sentiment, word-tokenization/\n")
        f.write("# License: CC0-1.0 — safe to commit and redistribute\n")
        f.write("# Format: word1<TAB>word2<TAB>count\n")
        f.write(f"# Minimum count: {args.min_count}\n")
        f.write(f"# Total bigram types: {len(kept):,}\n")
        f.write("#\n")
        for (w1, w2), c in sorted(kept.items(), key=lambda kv: -kv[1]):
            f.write(f"{w1}\t{w2}\t{c}\n")
    print(f"[done] {len(kept):,} bigrams -> {out}")


if __name__ == "__main__":
    main()
