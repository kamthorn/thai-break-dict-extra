#!/usr/bin/env python3
"""
scripts/analyze_errors.py
Attribute per-chunk segmentation regressions to extra-dictionary words.

Measurement only: reads the gold corpus locally, never copies corpus text
into the repository. LST20 (NECTEC) is used for scoring alone, per project
policy (see README IMPORTANT note).

Method: segment every chunk twice — base dict vs base+extra dict — with the
same engine. For chunks where base+extra scores LOWER word-F1 than base,
collect extra-only words (in extra dict, absent from base dict) present in
the worse prediction. Frequent offenders are curation candidates: they win
Viterbi paths against gold segmentation.

Usage:
  python3 scripts/analyze_errors.py --corpus-dir ../LST20_Corpus/eval \\
      --base-dict ../thai-break/data/words.txt --extra-dict dist/words-extra.tsv \\
      --segmenter-cmd "php ../thai-break/tools/segment.php {dict}" [--limit 2000]
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import (  # noqa: E402
    command_segmenter,
    lst20_chunks,
    merged_dictionary,
    prf,
    spans,
)


def chunk_f1(gold: list[str], pred: list[str]) -> float:
    gs, ps = spans(gold), spans(pred)
    if not gs and not ps:
        return 1.0
    _, _, f = prf(len(gs & ps), len(ps), len(gs))
    return f


def main() -> None:
    ap = argparse.ArgumentParser(description="Attribute regressions to extra words")
    ap.add_argument("--corpus-dir", type=Path, required=True)
    ap.add_argument("--base-dict", type=Path, required=True)
    ap.add_argument("--extra-dict", type=Path, required=True)
    ap.add_argument("--segmenter-cmd", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    chunks = list(lst20_chunks(args.corpus_dir))
    if args.limit:
        chunks = chunks[: args.limit]
    texts = ["".join(c) for c in chunks]

    base_path, base_words = merged_dictionary([args.base_dict])
    extra_path, _ = merged_dictionary([args.base_dict, args.extra_dict])
    extra_only = {w for w in open(extra_path, encoding="utf-8").read().split()
                  if w not in base_words and not w.startswith("#")}
    # merged temp dicts carry weights; re-read plain word forms for membership
    extra_only = {w.split("\t")[0] for w in extra_only}

    seg_base = command_segmenter(args.segmenter_cmd, base_path)
    seg_extra = command_segmenter(args.segmenter_cmd, extra_path)
    print(f"[info] segmenting {len(texts)} chunks x2 ...", flush=True)
    pred_base = seg_base(texts)
    pred_extra = seg_extra(texts)

    reg_counter: collections.Counter[str] = collections.Counter()
    reg_chunks = imp_chunks = same = 0
    examples: dict[str, list[str]] = collections.defaultdict(list)
    for gold, pb, pe, text in zip(chunks, pred_base, pred_extra, texts):
        if "".join(pe) != text or "".join(pb) != text:
            continue
        fb, fe = chunk_f1(gold, pb), chunk_f1(gold, pe)
        if fe < fb - 1e-9:
            reg_chunks += 1
            for tok in pe:
                if tok in extra_only:
                    reg_counter[tok] += 1
                    if len(examples[tok]) < 2:
                        examples[tok].append(text[:60])
        elif fe > fb + 1e-9:
            imp_chunks += 1
        else:
            same += 1

    print(f"[info] chunks: regressed={reg_chunks} improved={imp_chunks} same={same}")
    print(f"\nTop {args.top} extra words in regressed predictions "
          f"(word: regressed-chunk count):")
    for word, n in reg_counter.most_common(args.top):
        print(f"  {word} ({n})")
    print("\nExamples (first 10 offenders):")
    for word, _ in reg_counter.most_common(10):
        for ex in examples[word][:1]:
            print(f"  {word} <- {ex}")


if __name__ == "__main__":
    main()
