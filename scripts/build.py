#!/usr/bin/env python3
"""
scripts/build.py
Builds and combines categorized dictionary files into unified output files.
Can also merge with an existing base dictionary (e.g. from thai-break-service).
"""

import argparse
import os
import sys
from pathlib import Path
from collections import defaultdict

STRIP_CHARS = "\ufeff\u200b\u200c\u200d\u200e\u200f\r\n\t "


def load_words_from_file(filepath: Path) -> set[str]:
    words = set()
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            cleaned = line.strip(STRIP_CHARS)
            if cleaned and not cleaned.startswith("#"):
                words.add(cleaned)
    return words


def thai_sort_key(word: str):
    """
    Thai collation sorting key moving leading vowels (เ แ โ ใ ไ) after the consonant.
    """
    LEADING_VOWELS = "\u0e40\u0e41\u0e42\u0e43\u0e44"
    if word and word[0] in LEADING_VOWELS and len(word) > 1:
        return word[1] + word[0] + word[2:]
    return word


def main():
    parser = argparse.ArgumentParser(description="Build and merge thai-break-dict-extra dictionary.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Path to data directory (default: data)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/words-extra.txt"),
        help="Output path for extra dictionary (default: dist/words-extra.txt)",
    )
    parser.add_argument(
        "--base-dict",
        type=Path,
        default=None,
        help="Optional path to base dictionary (e.g. ../thai-break-service/data/words.txt)",
    )
    parser.add_argument(
        "--include",
        type=str,
        default=None,
        help="Comma-separated category names to include (e.g. 'transit,proper-names')",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default=None,
        help="Comma-separated category names to exclude (e.g. 'misspellings,slang')",
    )
    parser.add_argument(
        "--merged-output",
        type=Path,
        default=None,
        help="Optional output path for merged base + extra dictionary",
    )
    parser.add_argument(
        "--sort-method",
        choices=["codepoint", "thai"],
        default="codepoint",
        help="Sorting method: 'codepoint' (matching standard binary search/Rust UTF-8 order) or 'thai'",
    )

    args = parser.parse_args()

    data_dir = args.data_dir
    if not data_dir.exists():
        print(f"Error: Data directory not found at {data_dir}", file=sys.stderr)
        sys.exit(1)

    txt_files = sorted(data_dir.rglob("*.txt"))
    if not txt_files:
        print("Error: No .txt files found in data directory.", file=sys.stderr)
        sys.exit(1)

    include_cats = {c.strip() for c in args.include.split(",")} if args.include else None
    exclude_cats = {c.strip() for c in args.exclude.split(",")} if args.exclude else set()

    filtered_files = []
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
        filtered_files.append((fp, category))

    if not filtered_files:
        print("Error: No dictionary files matched the specified filter criteria.", file=sys.stderr)
        sys.exit(1)

    print(f"📦 Building extra dictionary from {len(filtered_files)} file(s) in {data_dir}...")

    category_stats = defaultdict(lambda: {"files": 0, "words": set()})
    all_extra_words = set()

    for file_path, category in filtered_files:
        words = load_words_from_file(file_path)
        category_stats[category]["files"] += 1
        category_stats[category]["words"].update(words)
        all_extra_words.update(words)

    # Print breakdown per category
    print("\n--- Category Breakdown ---")
    for category, stats in sorted(category_stats.items()):
        print(f"  • {category:<15} : {len(stats['words']):>6} words ({stats['files']} file(s))")
    print("--------------------------")
    print(f"Total Unique Extra Words : {len(all_extra_words):>6}\n")

    # Sort
    if args.sort_method == "thai":
        sorted_extra = sorted(all_extra_words, key=thai_sort_key)
    else:
        sorted_extra = sorted(all_extra_words)

    # Write extra output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8", newline="\n") as f:
        for word in sorted_extra:
            f.write(f"{word}\n")

    print(f"✓ Saved extra dictionary to: {args.output} ({len(sorted_extra)} words)")

    # Compare / Merge with base dictionary if provided
    if args.base_dict:
        if not args.base_dict.exists():
            print(f"Warning: Base dictionary file not found at {args.base_dict}", file=sys.stderr)
        else:
            base_words = load_words_from_file(args.base_dict)
            novel_words = all_extra_words - base_words
            overlap_words = all_extra_words & base_words

            print(f"\n--- Comparison with Base Dictionary ({args.base_dict}) ---")
            print(f"  • Base words count    : {len(base_words):>6}")
            print(f"  • Overlap words       : {len(overlap_words):>6}")
            print(f"  • Brand new words (+) : {len(novel_words):>6}")

            if args.merged_output:
                merged_words = base_words | all_extra_words
                if args.sort_method == "thai":
                    sorted_merged = sorted(merged_words, key=thai_sort_key)
                else:
                    sorted_merged = sorted(merged_words)

                args.merged_output.parent.mkdir(parents=True, exist_ok=True)
                with open(args.merged_output, "w", encoding="utf-8", newline="\n") as f:
                    for word in sorted_merged:
                        f.write(f"{word}\n")
                print(f"✓ Saved merged dictionary to: {args.merged_output} ({len(sorted_merged)} words)")

    print("\n🎉 Build completed successfully!")


if __name__ == "__main__":
    main()
