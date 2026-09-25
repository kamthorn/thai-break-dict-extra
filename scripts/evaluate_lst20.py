#!/usr/bin/env python3
"""
scripts/evaluate_lst20.py
Evaluates ThaiBreak word segmentation on the LST20 Corpus.
Compares Base Dictionary vs Base + Dict-Extra.
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Add PHPThaiNLP python binding
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "PHPThaiNLP" / "python"))
import thaibreak

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import evaluate  # noqa: E402
from corpora import lst20_file_chunks  # noqa: E402


def evaluate_split(files: list[Path], dict_path: str):
    """
    Evaluates word segmentation on given LST20 files using the specified dictionary.
    Chunks end at spaces and sentence boundaries (see corpora.lst20_file_chunks).
    """
    thaibreak.init(dict_path)
    chunks = [chunk for fn in files for chunk in lst20_file_chunks(fn)]
    result = evaluate(chunks, [thaibreak.words("".join(chunk)) for chunk in chunks])

    return {
        "boundary_p": result["boundary"]["precision"],
        "boundary_r": result["boundary"]["recall"],
        "boundary_f1": result["boundary"]["f1"],
        "word_p": result["word"]["precision"],
        "word_r": result["word"]["recall"],
        "word_f1": result["word"]["f1"],
        "words_true": result["gold_words"],
        "words_pred": result["predicted_words"],
        "words_correct": result["correct_words"],
    }


def find_concrete_examples(files: list[Path], base_dict: str, extra_dict: str, limit: int = 15):
    """
    Finds concrete clauses where segmentation differed between Base and Extra.
    """
    # Collect up to 150 short chunks (3-12 words) from the first 30 files
    clauses = []
    for fn in files[:30]:
        for chunk in lst20_file_chunks(fn):
            if 3 <= len(chunk) <= 12:
                clauses.append((chunk, "".join(chunk)))
        if len(clauses) >= 150:
            break

    examples = []
    # Test base
    thaibreak.init(base_dict)
    base_preds = [thaibreak.words(c[1]) for c in clauses]

    # Test extra
    thaibreak.init(extra_dict)
    extra_preds = [thaibreak.words(c[1]) for c in clauses]

    for (gold, raw), b_pred, e_pred in zip(clauses, base_preds, extra_preds):
        if b_pred != e_pred:
            # Check which one matched gold better
            gold_str = " | ".join(gold)
            b_str = " | ".join(b_pred)
            e_str = " | ".join(e_pred)
            b_correct = (b_pred == gold)
            e_correct = (e_pred == gold)
            examples.append({
                "raw": raw,
                "gold": gold_str,
                "base": b_str,
                "extra": e_str,
                "improved": e_correct and not b_correct,
            })
            if len(examples) >= limit:
                break

    return examples


def main():
    parser = argparse.ArgumentParser(description="Evaluate ThaiBreak on LST20 corpus.")
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=Path("../LST20_Corpus/eval"),
        help="Path to LST20 evaluation folder (default: ../LST20_Corpus/eval)",
    )
    parser.add_argument(
        "--base-dict",
        type=Path,
        default=Path("../PHPThaiNLP/data/words.txt"),
        help="Path to base dictionary",
    )
    parser.add_argument(
        "--extra-dict",
        type=Path,
        default=Path("dist/words-extra.txt"),
        help="Path to extra dictionary",
    )
    parser.add_argument(
        "--include",
        type=str,
        default=None,
        help="Comma-separated category names or file stems to include (e.g. 'transit,proper-names')",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default=None,
        help="Comma-separated category names or file stems to exclude (e.g. 'compounds,proper-names')",
    )
    parser.add_argument(
        "--limit-files",
        type=int,
        default=None,
        help="Limit number of files to evaluate (default: all)",
    )
    args = parser.parse_args()

    if not args.corpus_dir.exists():
        print(f"Error: Corpus directory {args.corpus_dir} not found.", file=sys.stderr)
        sys.exit(1)

    files = [f for f in sorted(args.corpus_dir.glob("*.txt")) if not f.name.startswith("._")]
    if args.limit_files:
        files = files[:args.limit_files]

    print(f"📊 Evaluating ThaiBreak on LST20 Corpus ({len(files)} files)...")

    # Create merged temp dict
    tmp_merged = Path("/tmp/thaibreak_eval_merged.txt")
    if args.include or args.exclude:
        data_dir = Path("data")
        txt_files = sorted(data_dir.rglob("*.txt"))
        include_cats = {c.strip() for c in args.include.split(",")} if args.include else None
        exclude_cats = {c.strip() for c in args.exclude.split(",")} if args.exclude else set()
        
        extra_words = set()
        for fp in txt_files:
            rel = fp.relative_to(data_dir)
            category = rel.parts[0] if len(rel.parts) > 1 else "root"
            matches_include = (not include_cats) or (
                category in include_cats or fp.stem in include_cats or rel.as_posix() in include_cats
            )
            matches_exclude = (
                category in exclude_cats or fp.stem in exclude_cats or rel.as_posix() in exclude_cats
            )
            if not matches_include or matches_exclude:
                continue
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    w = line.strip()
                    if w and not w.startswith("#"):
                        extra_words.add(w)

        with open(tmp_merged, "w", encoding="utf-8") as out:
            with open(args.base_dict, "r", encoding="utf-8") as f:
                out.write(f.read())
            for w in sorted(extra_words):
                out.write(f"{w}\n")
    else:
        with open(tmp_merged, "w", encoding="utf-8") as out:
            with open(args.base_dict, "r", encoding="utf-8") as f:
                out.write(f.read())
            with open(args.extra_dict, "r", encoding="utf-8") as f:
                out.write(f.read())

    print("1. Running Model 1: Standard Base Dictionary...")
    t0 = time.time()
    base_res = evaluate_split(files, str(args.base_dict))
    t1 = time.time()
    print(f"   Done in {t1 - t0:.2f}s")

    print("2. Running Model 2: Base + Dict-Extra...")
    t2 = time.time()
    extra_res = evaluate_split(files, str(tmp_merged))
    t3 = time.time()
    print(f"   Done in {t3 - t2:.2f}s")

    # Find concrete examples
    examples = find_concrete_examples(files, str(args.base_dict), str(tmp_merged), limit=8)

    # Print summary table
    print("\n" + "=" * 70)
    print("📈 LST20 BENCHMARK EVALUATION RESULTS")
    print("=" * 70)
    print(f"{'Metric':<30} | {'Base Dict':<12} | {'+ Dict-Extra':<12} | {'Change (Δ)':<10}")
    print("-" * 70)

    # Metrics
    metrics = [
        ("Word Boundary Precision", "boundary_p"),
        ("Word Boundary Recall", "boundary_r"),
        ("Word Boundary F1-Score", "boundary_f1"),
        ("Word Exact Match Precision", "word_p"),
        ("Word Exact Match Recall", "word_r"),
        ("Word Exact Match F1-Score", "word_f1"),
    ]

    for label, key in metrics:
        b_val = base_res[key] * 100
        e_val = extra_res[key] * 100
        diff = e_val - b_val
        diff_str = f"{diff:+.2f}%" if diff != 0 else "0.00%"
        print(f"{label:<30} | {b_val:>10.2f}% | {e_val:>10.2f}% | {diff_str:>10}")

    print("=" * 70)
    print(f"Ground Truth Words Evaluated : {base_res['words_true']:,}")
    print(f"Correct Words (Base)         : {base_res['words_correct']:,}")
    print(f"Correct Words (+ Dict-Extra) : {extra_res['words_correct']:,} ({extra_res['words_correct'] - base_res['words_correct']:+,} words)")
    print("=" * 70)

    print("\n🔍 CONCRETE EXAMPLES OF SEGMENTATION CHANGES:")
    for idx, ex in enumerate(examples, 1):
        status = "✨ IMPROVED (Matches Gold)" if ex["improved"] else "🔄 CHANGED"
        print(f"\nExample {idx}: [{status}]")
        print(f"  Raw Text     : {ex['raw']}")
        print(f"  Ground Truth : {ex['gold']}")
        print(f"  Base Dict    : {ex['base']}")
        print(f"  + Dict-Extra : {ex['extra']}")


if __name__ == "__main__":
    main()
