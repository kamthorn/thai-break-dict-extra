#!/usr/bin/env python3
"""
scripts/harvest_wikipedia_titles.py
Harvests clean Thai named entities, institutions, infrastructure, and domain terms
from the official Thai Wikipedia title dump (thwiki-latest-all-titles-in-ns0.gz).

Licensed under CC BY-SA 4.0 / Wikimedia Foundation.
"""

import gzip
import os
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

DUMP_URL = "https://dumps.wikimedia.org/thwiki/latest/thwiki-latest-all-titles-in-ns0.gz"
LOCAL_CACHE = Path(__file__).resolve().parent.parent / "local" / "thwiki-titles.gz"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

THAI_ONLY_RE = re.compile(r"^[\u0e01-\u0e4e\u0e4f\u0e50-\u0e59]+$")

# Generic root words that should not be added as extra words
STOP_ROOTS = {
    "มหาวิทยาลัย", "โรงเรียน", "กระทรวง", "กรม", "สำนักงาน", "วัด",
    "อุทยานแห่งชาติ", "ปราสาท", "ถนน", "สะพาน", "ทางหลวง", "สถานี",
    "สถานีรถไฟ", "พรรค", "โรงพยาบาล", "โรค", "กลุ่มอาการ"
}

CATEGORY_ROUTES = {
    "universities": DATA_DIR / "education" / "universities.txt",
    "schools": DATA_DIR / "education" / "schools.txt",
    "organizations": DATA_DIR / "proper-names" / "organizations.txt",
    "landmarks": DATA_DIR / "proper-names" / "landmarks.txt",
    "roads": DATA_DIR / "transit" / "roads.txt",
    "stations": DATA_DIR / "transit" / "stations.txt",
    "parties": DATA_DIR / "politics" / "parties.txt",
    "medical": DATA_DIR / "domains" / "medical.txt",
}


def download_dump():
    LOCAL_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if LOCAL_CACHE.exists() and LOCAL_CACHE.stat().st_size > 1_000_000:
        print(f"Using cached Wikipedia title dump: {LOCAL_CACHE}")
        return

    print(f"Downloading Thai Wikipedia title dump from:\n  {DUMP_URL}")
    req = urllib.request.Request(DUMP_URL, headers={"User-Agent": "ThaiBreakBot/1.0 (NLP Research)"})
    with urllib.request.urlopen(req) as resp, open(LOCAL_CACHE, "wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
    print(f"✓ Saved dump cache to: {LOCAL_CACHE} ({LOCAL_CACHE.stat().st_size:,} bytes)")


def classify_title(title: str) -> str | None:
    if title in STOP_ROOTS:
        return None
    if not THAI_ONLY_RE.match(title) or len(title) < 4 or len(title) > 28:
        return None

    if title.startswith("มหาวิทยาลัย"):
        return "universities"
    if title.startswith("โรงเรียน") and len(title) <= 25:
        return "schools"
    if title.startswith("กระทรวง") or title.startswith("กรม") or title.startswith("สำนักงาน"):
        return "organizations"
    if title.startswith("วัด") or title.startswith("อุทยานแห่งชาติ") or title.startswith("ปราสาท"):
        return "landmarks"
    if title.startswith("ถนน") or title.startswith("สะพาน") or title.startswith("ทางพิเศษ"):
        return "roads"
    if title.startswith("สถานีรถไฟ") or title.startswith("สถานี"):
        return "stations"
    if title.startswith("พรรค") and len(title) <= 20:
        return "parties"
    if title.startswith("โรงพยาบาล") or title.startswith("โรค"):
        return "medical"

    return None


def harvest_titles(limit_per_category: int = 500):
    download_dump()

    harvested = defaultdict(set)

    with gzip.open(LOCAL_CACHE, "rt", encoding="utf-8", errors="ignore") as gz:
        for line in gz:
            raw = line.strip()
            # Clean Wikipedia title: remove parenthetical disambiguation and replace underscores
            cleaned = re.sub(r"\(.*?\)", "", raw).replace("_", "").strip()

            target = classify_title(cleaned)
            if target:
                harvested[target].add(cleaned)

    print("\n--- Wikipedia Harvesting Summary ---")
    for cat, items in sorted(harvested.items()):
        target_file = CATEGORY_ROUTES[cat]
        existing = set()
        if target_file.exists():
            with open(target_file, "r", encoding="utf-8") as f:
                for l in f:
                    w = l.strip()
                    if w and not w.startswith("#"):
                        existing.add(w)

        # Cap new additions per category if limit provided to avoid noisy tail
        sorted_new = sorted(items)
        if limit_per_category and len(sorted_new) > limit_per_category:
            sorted_new = sorted_new[:limit_per_category]

        merged = existing | set(sorted_new)
        added = len(merged) - len(existing)

        # Write merged file
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "w", encoding="utf-8", newline="\n") as f:
            for w in sorted(merged):
                f.write(f"{w}\n")

        print(f"  • {cat:<15} : {len(merged):>5} words (+{added:>4} added) -> {target_file.name}")

    print("\n✓ Harvesting complete! Run scripts/format.py and scripts/build.py to apply.")


if __name__ == "__main__":
    harvest_titles()
