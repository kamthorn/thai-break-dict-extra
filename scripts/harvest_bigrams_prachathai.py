#!/usr/bin/env python3
"""
scripts/harvest_bigrams_prachathai.py
Extract word bigrams from Prachathai-67k news corpus (Apache-2.0).

Source: HuggingFace wannaphong/prachathai67k (parquet, 2 train shards)
  - 54,380 articles from Prachathai.com (2004-2018)
  - Columns: url, date, title, body_text, + 12 binary topic tags
  - License: Apache-2.0 (safe to commit derived statistics)

Method: tokenize title+body with the current ThaiBreak segmenter, then
count adjacent word pairs. This is a bootstrapping approach — the bigram
model learns the segmenter's own output distribution, which improves
consistency and resolves same-count ambiguities toward more natural
Thai word sequences.

Output: data/bigrams-prachathai.tsv  (word1<TAB>word2<TAB>count)
Raw parquet files are cached in local/ (gitignored).

Usage:
  python3 scripts/harvest_bigrams_prachathai.py [--min-count 5] [--output data/bigrams-prachathai.tsv]
"""

import argparse
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / "local"
OUTPUT = ROOT / "data" / "bigrams-prachathai.tsv"

HF_BASE = "https://huggingface.co/datasets/wannaphong/prachathai67k/resolve/main/data"
SHARDS = [
    "train-00000-of-00002.parquet",
    "train-00001-of-00002.parquet",
]

# Segmenter: use the merged FST from thai-break-service if available,
# else fall back to the base dict.
SEGMENTER_CANDIDATES = [
    ROOT.parent / "thai-break-service" / "data" / "words.fst",
    ROOT.parent / "thai-break" / "data" / "words.fst",
    ROOT.parent / "thai-break" / "data" / "words.txt",
]


def fetch_shard(name: str) -> Path:
    cached = LOCAL / name
    if cached.exists():
        print(f"[cache] {cached}")
        return cached
    url = f"{HF_BASE}/{name}"
    print(f"[fetch] {url}")
    LOCAL.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ThaiBreakHarvest/1.0"})
        with urllib.request.urlopen(req, timeout=300) as resp, open(cached, "wb") as f:
            f.write(resp.read())
    except Exception as e:
        print(f"[error] download failed: {e}", file=sys.stderr)
        sys.exit(1)
    return cached


def load_segmenter():
    sys.path.insert(0, str(ROOT.parent / "thai-break" / "python"))
    from thaibreak import core

    for path in SEGMENTER_CANDIDATES:
        if path.exists():
            print(f"[segmenter] {path}")
            core.init(str(path), None)
            return core
    sys.exit("Error: no segmenter dictionary found")


def main() -> None:
    ap = argparse.ArgumentParser(description="Harvest bigrams from Prachathai-67k")
    ap.add_argument("--min-count", type=int, default=5)
    ap.add_argument("--output", type=Path, default=OUTPUT)
    args = ap.parse_args()

    try:
        import pandas as pd
    except ImportError:
        sys.exit("Error: pandas + pyarrow required (pip install pandas pyarrow)")

    core = load_segmenter()

    bigrams: Counter = Counter()
    n_articles = 0
    n_tokens = 0

    for shard in SHARDS:
        path = fetch_shard(shard)
        df = pd.read_parquet(path)
        print(f"[info] {path.name}: {len(df):,} articles")

        for _, row in df.iterrows():
            title = str(row.get("title", "") or "")
            body = str(row.get("body_text", "") or "")
            text = (title + " " + body).strip()
            if not text:
                continue
            tokens = core.words(text)
            if len(tokens) < 2:
                continue
            n_articles += 1
            n_tokens += len(tokens)
            for i in range(len(tokens) - 1):
                bigrams[(tokens[i], tokens[i + 1])] += 1

    print(f"[info] {n_articles:,} articles, {n_tokens:,} tokens, {len(bigrams):,} raw bigram types")

    kept = {k: c for k, c in bigrams.items() if c >= args.min_count}
    print(f"[info] bigrams with count >= {args.min_count}: {len(kept):,}")

    out: Path = args.output
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Thai word bigrams from Prachathai-67k news corpus (Apache-2.0)\n")
        f.write("# Source: HuggingFace wannaphong/prachathai67k (train split)\n")
        f.write("# Tokenized with ThaiBreak segmenter (bootstrapping)\n")
        f.write("# License: Apache-2.0 — safe to commit and redistribute\n")
        f.write("# Format: word1<TAB>word2<TAB>count\n")
        f.write(f"# Minimum count: {args.min_count}\n")
        f.write(f"# Total bigram types: {len(kept):,}\n")
        f.write("#\n")
        for (w1, w2), c in sorted(kept.items(), key=lambda kv: -kv[1]):
            f.write(f"{w1}\t{w2}\t{c}\n")
    print(f"[done] {len(kept):,} bigrams -> {out}")


if __name__ == "__main__":
    main()
