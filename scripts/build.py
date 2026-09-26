#!/usr/bin/env python3
"""
scripts/build.py
Builds and combines categorized dictionary files into unified output files.
Generates both plain wordlists (.txt), weighted dictionaries (.tsv), and compact binary DAWG (.dawg).
Can also merge with an existing base dictionary (e.g. from thai-break).
"""

import argparse
import os
import struct
import sys
from pathlib import Path
from collections import defaultdict

STRIP_CHARS = "\ufeff\u200b\u200c\u200d\u200e\u200f\r\n\t "

# --- Tier Weight Configuration ---
DEFAULT_TIER_WEIGHTS = {
    # Tier 1: Fixed Proper Names, Countries & Months (Weight 6.0 - 8.0)
    "proper-names/provinces": 8.0,
    "abbreviations/months": 7.0,
    "proper-names/districts": 6.0,
    "proper-names/countries": 6.0,
    "transit/stations": 6.0,
    "proper-names/organizations": 5.0,
    "proper-names/landmarks": 5.0,
    "proper-names/persons": 5.0,
    "education/universities": 5.0,
    # Tier 2: Core News Compounds & Abbreviations
    "news/compounds": 4.5,
    "news/connectives": 4.0,
    "news/royal": 4.0,
    "abbreviations/ranks": 5.0,
    "abbreviations/titles": 5.0,
    "abbreviations/addresses": 5.0,
    "abbreviations/units": 4.0,
    "abbreviations/common": 4.0,
    "politics/parties": 4.0,
    "transit/roads": 4.5,
    # Tier 3: Domains & Technical Loanwords
    "domains/medical": 3.5,
    "domains/finance": 3.5,
    "domains/legal": 3.5,
    "education/schools": 3.5,
    "politics/society": 3.0,
    "culture/beliefs": 3.0,
    "culture/traditions": 3.0,
    "automotive/vehicles": 3.0,
    "environment/esg": 3.0,
    "loanwords/tech": 3.0,
    "loanwords/food": 3.0,
    "proper-names/brands": 3.5,
    # Tier 4: Pop-Culture & Slang
    "loanwords/general": 2.5,
    "pop-culture/gaming": 2.5,
    "pop-culture/anime-manga": 2.5,
    "slang/internet": 1.5,
    # Tier 5: Common Misspellings (Low weight to prioritize correct spellings)
    "misspellings/common": 0.5,
}

CATEGORY_DEFAULT_WEIGHTS = {
    "proper-names": 5.0,
    "abbreviations": 4.5,
    "news": 4.0,
    "transit": 4.5,
    "education": 4.0,
    "domains": 3.5,
    "politics": 3.0,
    "culture": 3.0,
    "automotive": 3.0,
    "environment": 3.0,
    "loanwords": 2.8,
    "pop-culture": 2.5,
    "slang": 1.5,
    "misspellings": 0.5,
}


def get_tier_weight(category: str, stem: str) -> float:
    key = f"{category}/{stem}"
    if key in DEFAULT_TIER_WEIGHTS:
        return DEFAULT_TIER_WEIGHTS[key]
    return CATEGORY_DEFAULT_WEIGHTS.get(category, 2.0)


def compute_word_weight(word: str, base_weight: float) -> float:
    """
    Applies length bias for long multi-syllable compound words (length >= 5 chars).
    """
    if base_weight >= 2.0 and len(word) >= 5:
        length_bonus = min(1.5, 0.1 * (len(word) - 4))
        return round(base_weight + length_bonus, 2)
    return round(base_weight, 2)


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


def build_dawg_from_words(words: list[str], output_path: str):
    """
    Compile a sorted unique wordlist into a Minimal DAWG (TBD1 format).
    """
    words = sorted(list(set(words)))

    class Node:
        __slots__ = ("edges", "is_final", "id")
        def __init__(self):
            self.edges = {}
            self.is_final = False
            self.id = 0

    root = Node()
    for w in words:
        curr = root
        for ch in w:
            if ch not in curr.edges:
                curr.edges[ch] = Node()
            curr = curr.edges[ch]
        curr.is_final = True

    # Bottom-up minimization (Daciuk's algorithm)
    node_signatures = {}
    def minimize(node):
        for ch, child in list(node.edges.items()):
            node.edges[ch] = minimize(child)
        sig = (node.is_final, tuple(sorted((ch, id(child)) for ch, child in node.edges.items())))
        if sig in node_signatures:
            return node_signatures[sig]
        node_signatures[sig] = node
        return node

    min_root = minimize(root)

    # Breadth-first traversal to assign contiguous state IDs (root = 0)
    states = [min_root]
    min_root.id = 0
    visited = {id(min_root)}

    queue = [min_root]
    while queue:
        curr = queue.pop(0)
        for ch, child in sorted(curr.edges.items()):
            if id(child) not in visited:
                child.id = len(states)
                visited.add(id(child))
                states.append(child)
                queue.append(child)

    buf = bytearray()
    buf.extend(b"TBD1")
    buf.extend(struct.pack("<II", len(states), len(words)))

    for s in states:
        is_final_bit = 0x80 if s.is_final else 0
        num_edges = len(s.edges)
        assert num_edges < 128, f"Too many edges in state {s.id}"
        buf.append(is_final_bit | num_edges)
        for ch, child in sorted(s.edges.items()):
            code = ord(ch)
            assert code <= 0xFFFF, f"Character {ch} exceeds uint16 BMP"
            buf.extend(struct.pack("<HH", code, child.id))

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(buf)

    out_size = len(buf)
    print(f"✓ Compiled binary DAWG: {output_path} ({out_size:,} bytes, {out_size/1024:.2f} KB)")


def compile_fst_if_available(tsv_path: Path, fst_path: Path) -> bool:
    """
    Compiles a weighted TSV dictionary into BurntSushi FST v3 format using thaibreak_compile_fst.
    """
    import shutil
    import subprocess

    candidates = [
        "thaibreak_compile_fst",
        str(Path(__file__).resolve().parent.parent.parent / "thai-break" / "rust" / "target" / "release" / "thaibreak_compile_fst"),
        str(Path(__file__).resolve().parent.parent.parent / "PHPThaiNLP" / "rust" / "target" / "release" / "thaibreak_compile_fst"),
    ]
    compiler = None
    for c in candidates:
        if shutil.which(c) or (Path(c).is_file() and os.access(c, os.X_OK)):
            compiler = c
            break

    if compiler:
        try:
            res = subprocess.run([compiler, str(tsv_path), str(fst_path)], capture_output=True, text=True, check=True)
            out_size = fst_path.stat().st_size
            print(f"✓ Compiled binary FST : {fst_path} ({out_size:,} bytes, {out_size/1024:.2f} KB)")
            return True
        except Exception as e:
            print(f"Warning: Failed to compile FST: {e}", file=sys.stderr)
    return False


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
        help="Optional path to base dictionary (e.g. ../thai-break/data/words.txt)",
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
        "--weights-mode",
        choices=["tier", "uniform"],
        default="tier",
        help="Weight calculation mode: 'tier' (linguistic category tiers) or 'uniform' (all 1.0)",
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
    parser.add_argument(
        "--compile-dawg",
        action="store_true",
        default=True,
        help="Automatically compile binary DAWG (.dawg) into dist/ (default: True)",
    )
    parser.add_argument(
        "--compile-fst",
        action="store_true",
        default=True,
        help="Automatically compile binary FST (.fst) if thaibreak_compile_fst is available (default: True)",
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
        filtered_files.append((fp, category, fp.stem))

    if not filtered_files:
        print("Error: No dictionary files matched the specified filter criteria.", file=sys.stderr)
        sys.exit(1)

    print(f"📦 Building extra dictionary from {len(filtered_files)} file(s) in {data_dir} (Weights: {args.weights_mode})...")

    category_stats = defaultdict(lambda: {"files": 0, "words": set()})
    word_weights: dict[str, float] = {}

    for file_path, category, stem in filtered_files:
        words = load_words_from_file(file_path)
        category_stats[category]["files"] += 1
        category_stats[category]["words"].update(words)

        base_tier_weight = get_tier_weight(category, stem) if args.weights_mode == "tier" else 1.0

        for w in words:
            w_weight = compute_word_weight(w, base_tier_weight) if args.weights_mode == "tier" else 1.0
            # Keep the highest weight if word appears in multiple categories
            if w not in word_weights or w_weight > word_weights[w]:
                word_weights[w] = w_weight

    all_extra_words = set(word_weights.keys())

    # Print breakdown per category
    print("\n--- Category Breakdown ---")
    for category, stats in sorted(category_stats.items()):
        tier_w = CATEGORY_DEFAULT_WEIGHTS.get(category, 1.0) if args.weights_mode == "tier" else 1.0
        print(f"  • {category:<15} : {len(stats['words']):>6} words ({stats['files']} file(s), Tier weight ~{tier_w})")
    print("--------------------------")
    print(f"Total Unique Extra Words : {len(all_extra_words):>6}\n")

    # Sort
    if args.sort_method == "thai":
        sorted_extra = sorted(all_extra_words, key=thai_sort_key)
    else:
        sorted_extra = sorted(all_extra_words)

    # 1. Write plain text wordlist (.txt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8", newline="\n") as f:
        for word in sorted_extra:
            f.write(f"{word}\n")
    print(f"✓ Saved plain text dictionary: {args.output} ({len(sorted_extra)} words)")

    # 2. Write weighted TSV dictionary (.tsv)
    tsv_output = args.output.with_suffix(".tsv")
    with open(tsv_output, "w", encoding="utf-8", newline="\n") as f:
        for word in sorted_extra:
            f.write(f"{word}\t{word_weights[word]:.2f}\n")
    print(f"✓ Saved weighted TSV dictionary: {tsv_output} ({len(sorted_extra)} words)")

    # 3. Compile binary DAWG (.dawg)
    if args.compile_dawg:
        dawg_output = args.output.with_suffix(".dawg")
        build_dawg_from_words(sorted_extra, str(dawg_output))

    # 4. Compile binary FST (.fst)
    if args.compile_fst:
        fst_output = args.output.with_suffix(".fst")
        compile_fst_if_available(tsv_output, fst_output)

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
                print(f"✓ Saved merged dictionary: {args.merged_output} ({len(sorted_merged)} words)")

                # Also save merged TSV
                merged_tsv = args.merged_output.with_suffix(".tsv")
                with open(merged_tsv, "w", encoding="utf-8", newline="\n") as f:
                    for word in sorted_merged:
                        w_val = word_weights.get(word, 1.0)
                        f.write(f"{word}\t{w_val:.2f}\n")
                print(f"✓ Saved merged TSV dictionary: {merged_tsv} ({len(sorted_merged)} words)")

    print("\n🎉 Build completed successfully!")


if __name__ == "__main__":
    main()
