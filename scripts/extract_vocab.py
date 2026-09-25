#!/usr/bin/env python3
"""
scripts/extract_vocab.py
Count the Thai words of a gold corpus split, for local experiments only.

The output goes to local/ (git-ignored). Corpus-derived word lists and
frequencies must not be committed or copied into data/ or dist/ until the
corpus license allows it (the LST20 agreement restricts derived use).

Example:
  python3 scripts/extract_vocab.py --corpus lst20 --corpus-dir ../LST20_Corpus/train \\
      --base-dict ../PHPThaiNLP/data/words.txt
  # -> local/lst20-train-vocab.tsv      word<TAB>count, all Thai words
  # -> local/lst20-train-new-words.tsv  words missing from the base dictionary
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpora import THAI_WORD, blackboard_chunks, lst20_chunks  # noqa: E402

LOCAL_DIR = Path(__file__).resolve().parent.parent / "local"


def count_words(chunks) -> collections.Counter[str]:
    counts: collections.Counter[str] = collections.Counter()
    for chunk in chunks:
        counts.update(w for w in chunk if THAI_WORD.match(w))
    return counts


def write_tsv(path: Path, items) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for word, count in items:
            f.write(f"{word}\t{count}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Count Thai words of a corpus split into local/ (not committed).")
    parser.add_argument("--corpus", choices=["lst20", "blackboard"], required=True)
    parser.add_argument("--corpus-dir", type=Path, required=True)
    parser.add_argument("--subword", action="store_true", help="Blackboard: count sub-words")
    parser.add_argument("--base-dict", type=Path, help="Also list words missing from this dictionary")
    parser.add_argument("--name", help="Output name prefix (default: <corpus>-<directory name>)")
    args = parser.parse_args()

    chunks = (lst20_chunks(args.corpus_dir) if args.corpus == "lst20"
              else blackboard_chunks(args.corpus_dir, subword=args.subword))
    counts = count_words(chunks)
    name = args.name or f"{args.corpus}-{args.corpus_dir.name}"

    vocab_path = LOCAL_DIR / f"{name}-vocab.tsv"
    write_tsv(vocab_path, counts.most_common())
    print(f"{vocab_path}: {len(counts)} words, {sum(counts.values())} tokens")

    if args.base_dict:
        base = {line.strip() for line in args.base_dict.read_text(encoding="utf-8").splitlines()}
        new_words = [(w, n) for w, n in counts.most_common() if w not in base]
        new_path = LOCAL_DIR / f"{name}-new-words.tsv"
        write_tsv(new_path, new_words)
        covered = sum(n for w, n in counts.items() if w in base) / max(1, sum(counts.values()))
        print(f"{new_path}: {len(new_words)} words not in {args.base_dict} (token coverage {covered:.1%})")


if __name__ == "__main__":
    main()
