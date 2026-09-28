#!/usr/bin/env python3
"""
scripts/curate_thai2fit.py
Curate data/general/thai2fit.txt without needing any licensed corpus.

Problems fixed:
  1. Misspellings at Tier-3.5 weight (2.0) outranking correct base forms,
     e.g. กฏจราจร beating กฎ — demoted to misspellings/common.txt (0.5).
  2. Multi-word phrases as dictionary units (ไปกินกัน, ไม่ชอบ, สวยกว่า),
     which fragment gold segmentation — REMOVED (pieces compose from base).
  3. Nickname / utterance fragments and ambiguous dotless scraps — REMOVED.
  4. Profanity and slang clippings in the general bucket — moved to slang/.
  5. Miscategorized proper nouns (แสนสิริ, เพื่อไทย) — moved to brands/parties.

Phrase rule: a token fully segmentable into >= 2 base-dict pieces (each
len >= 2) with at least one piece in FUNCTION_WORDS, and attested in NEITHER
PyThaiNLP words_th (CC0) NOR any other data/ category, is productive syntax
rather than a lexical unit -> remove. Lexicalized compounds (ตัวเอง, มากมาย,
กันน้ำ, น่ารัก, ...) survive via the attestation guard.

Usage:
  python3 scripts/curate_thai2fit.py --dry-run   # review only
  python3 scripts/curate_thai2fit.py             # apply + report
"""

import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
THAI2FIT = DATA / "general" / "thai2fit.txt"
MISSPELLINGS = DATA / "misspellings" / "common.txt"
SLANG = DATA / "slang" / "internet.txt"
BRANDS = DATA / "proper-names" / "brands.txt"
PARTIES = DATA / "politics" / "parties.txt"

BASE_DICT = ROOT.parent / "thai-break" / "data" / "words.txt"
WORDS_TH = Path("/home/kamthorn/code/pythainlp/pythainlp/corpus/words_th.txt")

DRY_RUN = "--dry-run" in sys.argv

# Closed-class function pieces that never form lexical units on their own.
FUNCTION_WORDS = {
    "ไป", "มา", "อยาก", "จะ", "ไม่", "ได้", "ต้อง", "ให้", "กับ", "และ",
    "ใน", "ของ", "จาก", "ถึง", "เพื่อ", "แต่", "หรือ", "ถ้า", "กว่า",
    "ว่า", "นี้", "กัน", "ด้วย", "เลย", "แล้ว", "ที่", "ซึ่ง", "โดย",
    "สำหรับ", "ระหว่าง", "ตั้งแต่", "จน", "เพราะ", "เมื่อ", "ก็", "จึง",
    "ขอ", "คือ", "อะไร", "สิ", "ไหน", "ละ", "เอง", "แค่", "น่า", "ห้าม",
    "อย่า", "ทุก", "ต่อ", "ขึ้น", "โมง", "ผม", "ฟรี",
    "ครับ", "ค่ะ", "คะ", "นะ", "ไหม", "มั้ย", "นี่",
}

# Orthographic misspelling transforms (applied as substrings).
TRANSFORMS = [
    ("กฏ", "กฎ"),
    ("ปรากฎ", "ปรากฏ"),
    ("สังเกตุ", "สังเกต"),
    ("อนุญาติ", "อนุญาต"),
    ("เว็ป", "เว็บ"),
    ("คลิ๊ก", "คลิก"),
    ("เฟ็ค", "เฟกต์"),
    ("ฟท์", "ฟต์"),
    ("เฟ่", "เฟต์"),
]

# Explicit (wrong, right) pairs; right must be in base dict.
PAIRS = [
    ("หมูกะทะ", "หมูกระทะ"),
    ("แมคโดนัล", "แมคโดนัลด์"),
    ("ดีแมก", "ดีแม็กซ์"),
    ("ดีแมค", "ดีแม็กซ์"),
    ("ดีแม็ก", "ดีแม็กซ์"),
    ("แมทท์", "แมตต์"),
    ("ฟิคซ์", "ฟิกซ์"),
    ("อัพ", "อัป"),
    ("การเเสดง", "การแสดง"),
    ("บาาท", "บาท"),
    ("โอ้ยย", "โอ๊ย"),
    ("ฮืออ", "ฮือ"),
    ("ค่าา", "ค่า"),
    ("บร้า", "บ้า"),
    ("สเมอนอฟ", "สเมอร์นอฟ"),
]

# Nickname / utterance fragments / ambiguous scraps: drop outright.
REMOVE = {
    "เติ้ล", "เต้ย", "ชลาทิศ", "โชติกา", "น้องลีโอ",
    "คุณจั้ม", "คุณลค", "คุณวิน", "แอดฯชัช",
    "เบียร์กู", "เบียร์ยู", "อิ", "ฅคนรักรถ", "ขวดน๊าา", "คลิ๊กเพจ",
}

# Profanity / clippings / laughter: general bucket is wrong, slang fits.
MOVE_TO_SLANG = {
    "อิดอก", "อิสัส", "อิเหี้ย", "อีควาย", "อีสัส", "อีเหี้ย",
    "สัส", "เยสเข้", "หุหุ", "เคร",
}

MOVE_TO_BRANDS = {"แสนสิริ"}
MOVE_TO_PARTIES = {"เพื่อไทย"}


def load_words(path: Path) -> set[str]:
    words = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            w = line.strip().lstrip("﻿")
            if w and not w.startswith("#"):
                words.add(w)
    return words


def main() -> None:
    base = load_words(BASE_DICT)
    print(f"[info] base dict: {len(base):,} words")
    missing_fn = FUNCTION_WORDS - base
    if missing_fn:
        print(f"[warn] function words not in base (rule degrades): {sorted(missing_fn)}")
    words_th = load_words(WORDS_TH) if WORDS_TH.exists() else set()
    print(f"[info] words_th (CC0): {len(words_th):,} words")

    others: set[str] = set()
    for fp in sorted(DATA.rglob("*.txt")):
        if fp == THAI2FIT:
            continue
        others |= load_words(fp)
    print(f"[info] words in other categories: {len(others):,}")

    t2f = [w for w in (l.strip() for l in THAI2FIT.read_text(encoding="utf-8").splitlines())
           if w and not w.startswith("#")]
    print(f"[info] thai2fit candidates: {len(t2f):,}")

    @lru_cache(maxsize=None)
    def segmentable(word: str) -> list[str] | None:
        """Split word into >= 2 base pieces (each len >= 2), else None."""
        n = len(word)
        memo: dict[int, list[str] | None] = {}

        def rec(i: int) -> list[str] | None:
            if i == n:
                return []
            if i in memo:
                return memo[i]
            for j in range(i + 2, n + 1):
                piece = word[i:j]
                if piece in base:
                    rest = rec(j)
                    if rest is not None:
                        memo[i] = [piece] + rest
                        return memo[i]
            memo[i] = None
            return None

        parts = rec(0)
        return parts if parts and len(parts) >= 2 else None

    to_misspell: dict[str, str] = {}
    to_remove: dict[str, str] = {}
    to_slang: set[str] = set()
    to_brands: set[str] = set()
    to_parties: set[str] = set()

    for w in t2f:
        if w in REMOVE:
            to_remove[w] = "explicit fragment/nickname list"
            continue
        if w in MOVE_TO_SLANG:
            to_slang.add(w)
            continue
        if w in MOVE_TO_BRANDS:
            to_brands.add(w)
            continue
        if w in MOVE_TO_PARTIES:
            to_parties.add(w)
            continue
        if w in base:
            continue  # base words need no curation (guardrail-capped anyway)
        # Rule 1: verified misspelling -> demote.
        corrected = w
        for wrong, right in TRANSFORMS:
            corrected = corrected.replace(wrong, right)
        pair_hit = next((r for bad, r in PAIRS if bad == w), None)
        if pair_hit is not None:
            corrected = pair_hit
        if corrected != w and corrected in base:
            to_misspell[w] = corrected
            continue
        if (corrected != w and w not in words_th and w not in others):
            # Orthographically suspicious (known-misspelling pattern) and
            # attested nowhere else -> demote even though the corrected
            # form itself is not in the base dictionary.
            to_misspell[w] = corrected + " (unverified)"
            continue
        # Rule 2: productive-syntax phrase -> remove.
        parts = segmentable(w)
        if (parts is not None
                and any(p in FUNCTION_WORDS for p in parts)
                and w not in words_th
                and w not in others):
            to_remove[w] = f"phrase [{'|'.join(parts)}]"
            continue

    print(f"\nMisspellings -> misspellings/common.txt ({len(to_misspell)}):")
    for w, c in sorted(to_misspell.items()):
        print(f"  {w} -> {c}")
    print(f"\nPhrases/fragments REMOVE ({len(to_remove)}):")
    for w, why in sorted(to_remove.items()):
        print(f"  {w}  [{why}]")
    print(f"\nMove -> slang/internet.txt ({len(to_slang)}): {sorted(to_slang)}")
    print(f"Move -> proper-names/brands.txt ({len(to_brands)}): {sorted(to_brands)}")
    print(f"Move -> politics/parties.txt ({len(to_parties)}): {sorted(to_parties)}")
    kept = len(t2f) - len(to_misspell) - len(to_remove) - len(to_slang) - len(to_brands) - len(to_parties)
    print(f"\nKept in general/thai2fit.txt: {kept}")

    if DRY_RUN:
        print("\n[dry-run] no files changed")
        return

    kept_words = [w for w in t2f
                  if w not in to_misspell and w not in to_remove
                  and w not in to_slang and w not in to_brands and w not in to_parties]
    THAI2FIT.write_text("".join(w + "\n" for w in sorted(set(kept_words))), encoding="utf-8")

    def append_unique(path: Path, words: set[str]) -> int:
        existing = load_words(path)
        new = sorted(w for w in words if w not in existing)
        if new:
            with open(path, "a", encoding="utf-8") as f:
                for w in new:
                    f.write(w + "\n")
        return len(new)

    n1 = append_unique(MISSPELLINGS, set(to_misspell))
    n2 = append_unique(SLANG, to_slang)
    n3 = append_unique(BRANDS, to_brands)
    n4 = append_unique(PARTIES, to_parties)
    print(f"\n[done] thai2fit={len(set(kept_words))}, +misspellings={n1}, "
          f"+slang={n2}, +brands={n3}, +parties={n4}")
    print("Next: python3 scripts/format.py && python3 scripts/validate.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
