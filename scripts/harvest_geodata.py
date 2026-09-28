#!/usr/bin/env python3
"""
scripts/harvest_geodata.py
Harvests official Thai administrative provinces, districts (Amphoe/Khet),
and subdistricts (Tambon/Khwaeng) from open government geodata datasets
(thailand-geography-json / DOPA / thai-province-data).

Outputs cleaned, validated names into:
  - data/proper-names/provinces.txt
  - data/proper-names/districts.txt
  - data/proper-names/subdistricts.txt
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

PROVINCES_URL = "https://raw.githubusercontent.com/thailand-geography-data/thailand-geography-json/main/src/provinces.json"
DISTRICTS_URL = "https://raw.githubusercontent.com/thailand-geography-data/thailand-geography-json/main/src/districts.json"
SUBDISTRICTS_URL = "https://raw.githubusercontent.com/thailand-geography-data/thailand-geography-json/main/src/subdistricts.json"

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "proper-names"
PROVINCES_FILE = DATA_DIR / "provinces.txt"
DISTRICTS_FILE = DATA_DIR / "districts.txt"
SUBDISTRICTS_FILE = DATA_DIR / "subdistricts.txt"

# Generic words that are too ambiguous when stand-alone as isolated 1-2 character words
STOP_WORDS = {
    "เมือง", "ใหม่", "กลาง", "ทอง", "สูง", "เหนือ", "ใต้", "ออก", "ตก", "ใน", "นอก",
}

DISTRICT_PREFIX_RE = re.compile(r"^(อำเภอ|เขต)")
SUBDISTRICT_PREFIX_RE = re.compile(r"^(ตำบล|แขวง)")
THAI_WORD_RE = re.compile(r"^[\u0e01-\u0e5b]+$")


def fetch_json(url: str):
    print(f"Fetching: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "ThaiBreak-Harvester/1.0"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_existing(file_path: Path) -> set[str]:
    existing = set()
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w and not w.startswith("#"):
                    existing.add(w)
    return existing


def save_words(file_path: Path, words: set[str]):
    sorted_words = sorted(words)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        for w in sorted_words:
            f.write(f"{w}\n")
    print(f"✓ Saved {len(sorted_words):,} words to {file_path.name}")


def harvest_provinces():
    data = fetch_json(PROVINCES_URL)
    existing = load_existing(PROVINCES_FILE)
    provinces = set(existing)

    for item in data:
        name = item.get("provinceNameTh", "").strip()
        if name and THAI_WORD_RE.match(name):
            provinces.add(name)

    # Ensure Bangkok short forms
    provinces.add("กรุงเทพฯ")
    provinces.add("กรุงเทพมหานคร")

    save_words(PROVINCES_FILE, provinces)


def harvest_districts():
    data = fetch_json(DISTRICTS_URL)
    existing = load_existing(DISTRICTS_FILE)
    districts = set(existing)

    for item in data:
        raw_name = item.get("districtNameTh", "").strip()
        if not raw_name:
            continue

        clean_name = DISTRICT_PREFIX_RE.sub("", raw_name).strip()

        for cand in [clean_name, raw_name]:
            if not cand or cand in STOP_WORDS:
                continue
            if not THAI_WORD_RE.match(cand):
                continue
            if len(cand) < 2:
                continue
            districts.add(cand)

    save_words(DISTRICTS_FILE, districts)


def harvest_subdistricts():
    data = fetch_json(SUBDISTRICTS_URL)
    existing = load_existing(SUBDISTRICTS_FILE)
    subdistricts = set(existing)

    for item in data:
        raw_name = item.get("subdistrictNameTh", "").strip()
        if not raw_name:
            continue

        clean_name = SUBDISTRICT_PREFIX_RE.sub("", raw_name).strip()

        for cand in [clean_name, raw_name]:
            if not cand or cand in STOP_WORDS:
                continue
            if not THAI_WORD_RE.match(cand):
                continue
            # Subdistricts must have length >= 3 to prevent over-eager short morpheme clashes
            if len(cand) < 3:
                continue
            subdistricts.add(cand)

    save_words(SUBDISTRICTS_FILE, subdistricts)


def main():
    print("=== Harvesting Thailand Geographic Vocabulary ===")
    harvest_provinces()
    harvest_districts()
    harvest_subdistricts()
    print("✓ Geodata harvesting complete!")


if __name__ == "__main__":
    main()
