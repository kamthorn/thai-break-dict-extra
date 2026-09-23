#!/usr/bin/env python3
"""
scripts/evaluate_lst20.py
Evaluates ThaiBreak word segmentation on the LST20 Corpus.
Compares Base Dictionary vs Base + Dict-Extra.
"""

import argparse
import glob
import os
import sys
import time
from pathlib import Path
from collections import Counter

# Add PHPThaiNLP python binding
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "PHPThaiNLP" / "python"))
import thaibreak


def evaluate_split(files: list[Path], dict_path: str):
    """
    Evaluates word segmentation on given LST20 files using the specified dictionary.
    """
    thaibreak.init(dict_path)
    
    total_true_b = 0
    total_pred_b = 0
    correct_b = 0

    words_true = 0
    words_pred = 0
    words_correct = 0

    # Collect word segmentation diffs
    fixed_words = Counter()
    split_words = Counter()

    for fn in files:
        with open(fn, "r", encoding="utf-8", errors="ignore") as f:
            chunk = []
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    w = parts[0]
                    if w == "_":
                        if chunk:
                            raw_text = "".join(chunk)
                            
                            # Boundary evaluation
                            b_true = set()
                            pos = 0
                            for t in chunk[:-1]:
                                pos += len(t)
                                b_true.add(pos)

                            preds = thaibreak.words(raw_text)
                            b_pred = set()
                            pos = 0
                            for t in preds[:-1]:
                                pos += len(t)
                                b_pred.add(pos)

                            total_true_b += len(b_true)
                            total_pred_b += len(b_pred)
                            correct_b += len(b_true & b_pred)

                            # Word-level span evaluation
                            words_true += len(chunk)
                            words_pred += len(preds)
                            
                            s_true = set()
                            p = 0
                            for t in chunk:
                                s_true.add((p, p + len(t), t))
                                p += len(t)

                            s_pred = set()
                            p = 0
                            for t in preds:
                                s_pred.add((p, p + len(t), t))
                                p += len(t)

                            # Match on spans (p_start, p_end)
                            true_spans = {(s[0], s[1]) for s in s_true}
                            pred_spans = {(s[0], s[1]) for s in s_pred}
                            words_correct += len(true_spans & pred_spans)

                            chunk = []
                    else:
                        chunk.append(w)

    bp = correct_b / total_pred_b if total_pred_b else 0
    br = correct_b / total_true_b if total_true_b else 0
    bf1 = 2 * bp * br / (bp + br) if (bp + br) else 0

    wp = words_correct / words_pred if words_pred else 0
    wr = words_correct / words_true if words_true else 0
    wf1 = 2 * wp * wr / (wp + wr) if (wp + wr) else 0

    return {
        "boundary_p": bp,
        "boundary_r": br,
        "boundary_f1": bf1,
        "word_p": wp,
        "word_r": wr,
        "word_f1": wf1,
        "words_true": words_true,
        "words_pred": words_pred,
        "words_correct": words_correct,
    }


def find_concrete_examples(files: list[Path], base_dict: str, extra_dict: str, limit: int = 15):
    """
    Finds concrete clauses where segmentation differed between Base and Extra.
    """
    thaibreak.init(base_dict)
    base_results = {}
    
    # Store first 100 clauses
    clauses = []
    for fn in files[:30]:
        with open(fn, "r", encoding="utf-8", errors="ignore") as f:
            chunk = []
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    w = parts[0]
                    if w == "_":
                        if len(chunk) >= 3 and len(chunk) <= 12:
                            raw = "".join(chunk)
                            clauses.append((chunk, raw))
                        chunk = []
                    else:
                        chunk.append(w)
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
        default=Path("../thai-break-service/data/words.txt"),
        help="Path to base dictionary",
    )
    parser.add_argument(
        "--extra-dict",
        type=Path,
        default=Path("dist/words-extra.txt"),
        help="Path to extra dictionary",
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
    print(f"Correct Words (+ Dict-Extra) : {extra_res['words_correct']:,} (+{extra_res['words_correct'] - base_res['words_correct']:,} words)")
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
