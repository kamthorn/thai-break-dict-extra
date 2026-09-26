#!/usr/bin/env python3
"""
scripts/harvest_geodata.py
Harvests official Thai administrative districts (Amphoe & Khet) from Open Government Data
(DOPA / kongvut/thai-province-data open dataset).

Outputs cleaned, validated district names into data/proper-names/districts.txt.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

DATA_URL = "https://raw.githubusercontent.com/kongvut/thai-province-data/master/api/latest/district.json"
DISTRICTS_FILE = Path(__file__).resolve().parent.parent / "data" / "proper-names" / "districts.txt"

# Generic words that are too ambiguous when stand-alone as 1-2 character words
STOP_WORDS = {
    "เมือง", "ใหม่", "กลาง", "ทอง", "สูง", "เหนือ", "ใต้", "ออก", "ตก",
}

PREFIX_RE = re.compile(r"^(อำเภอ|เขต)")
THAI_WORD_RE = re.compile(r"^[\u0e01-\u0e5b]+$")


def harvest_districts():
    print(f"Fetching official district dataset from:\n  {DATA_URL}")
    req = urllib.request.Request(DATA_URL, headers={"User-Agent": "ThaiBreak-Harvester/1.0"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    print(f"Loaded {len(data)} administrative records.")

    existing_districts = set()
    if DISTRICTS_FILE.exists():
        with open(DISTRICTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w and not w.startswith("#"):
                    existing_districts.add(w)

    print(f"Existing districts in {DISTRICTS_FILE.name}: {len(existing_districts)}")

    new_names = set(existing_districts)

    for item in data:
        raw_name = item.get("name_th", "").strip()
        if not raw_name:
            continue

        clean_name = PREFIX_RE.sub("", raw_name).strip()

        # Add both full name if common and stripped name
        for cand in [clean_name, raw_name]:
            if not cand or cand in STOP_WORDS:
                continue
            if not THAI_WORD_RE.match(cand):
                continue
            if len(cand) < 2:
                continue
            new_names.add(cand)

    print(f"Total districts after harvesting: {len(new_names)} (+{len(new_names) - len(existing_districts)} new)")

    # Sort
    sorted_names = sorted(new_names)

    with open(DISTRICTS_FILE, "w", encoding="utf-8", newline="\n") as f:
        for name in sorted_names:
            f.write(f"{name}\n")

    print(f"✓ Saved updated districts to: {DISTRICTS_FILE}")


if __name__ == "__main__":
    harvest_districts()
