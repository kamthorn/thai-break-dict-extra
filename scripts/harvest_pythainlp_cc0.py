#!/usr/bin/env python3
"""
scripts/harvest_pythainlp_cc0.py
Harvests open-licensed / public-domain datasets from PyThaiNLP and public domain sources:
- Official country names in Thai (countries_th.txt - CC0 1.0) -> data/proper-names/countries.txt
- Standard legal terminology from official Thai statutes -> data/domains/legal.txt
"""

import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

COUNTRIES_URL = "https://raw.githubusercontent.com/PyThaiNLP/pythainlp/dev/pythainlp/corpus/countries_th.txt"

THAI_ONLY_RE = re.compile(r"^[\u0e01-\u0e4e\u0e4f\u0e50-\u0e59]+$")

# Standard Thai legal terminology (Public domain under Section 7 of Thai Copyright Act)
LEGAL_TERMS = [
    "กรรมสิทธิ์", "ครอบครองปรปักษ์", "ปรปักษ์", "บุคคลธรรมดา", "นิติบุคคล",
    "ผู้แทนโดยชอบธรรม", "ผู้ใช้อำนาจปกครอง", "ผู้อนุบาล", "ผู้พิทักษ์",
    "คนไร้ความสามารถ", "คนเสมือนไร้ความสามารถ", "สาบสูญ", "การสาบสูญ",
    "ศาลแรงงาน", "ศาลแรงงานกลาง", "ศาลล้มละลาย", "ศาลล้มละลายกลาง",
    "ล้มละลาย", "ฟื้นฟูกิจการ", "พิทักษ์ทรัพย์", "พิทักษ์ทรัพย์เด็ดขาด",
    "ประนอมหนี้", "เจ้าพนักงานพิทักษ์ทรัพย์", "เจ้าพนักงานบังคับคดี",
    "พนักงานอัยการ", "อัยการสูงสุด", "สำนักงานอัยการสูงสุด", "ทนายความ",
    "สภาทนายความ", "เนติบัณฑิต", "เนติบัณฑิตยสภา", "ผู้เสียหาย", "ผู้ต้องหา",
    "จำเลยร่วม", "ร่วมกันกระทำความผิด", "ผู้สนับสนุน", "ตัวการ", "ผู้ใช้ให้กระทำความผิด",
    "พยายามกระทำความผิด", "เจตนา", "ประมาท", "บันดาลโทสะ", "ป้องกันโดยชอบด้วยกฎหมาย",
    "กระทำด้วยความจำเป็น", "คดีมีมูล", "ไต่สวนมูลฟ้อง", "ชี้สองสถาน", "สืบพยาน",
    "สืบพยานโจทก์", "สืบพยานจำเลย", "คำพิพากษา", "คำสั่งศาล", "หมายจับ",
    "หมายเรียก", "หมายค้น", "ฝากขัง", "ปล่อยชั่วคราว", "คำแถลงการณ์",
    "ฎีกา", "อุทธรณ์", "เพิกถอนสิทธิ", "ริบทรัพย์", "กักขังแทนค่าปรับ",
    "คุมประพฤติ", "รอการกำหนดโทษ", "รอการลงโทษ", "อาญาแผ่นดิน",
    "ความผิดอันยอมความได้", "ยอมความ", "ถอนคำร้องทุกข์", "ร้องทุกข์", "กล่าวโทษ",
    "สินสมรส", "สินส่วนตัว", "การสมรสซ้อน", "จดทะเบียนสมรส", "จดทะเบียนหย่า",
    "สิทธิเรียกร้อง", "การรับสภาพหนี้", "แปลงหนี้ใหม่", "ปลดเปลื้องหนี้",
    "ประมวลกฎหมายอาญา", "ประมวลกฎหมายแพ่งและพาณิชย์",
    "ประมวลกฎหมายวิธีพิจารณาความอาญา", "ประมวลกฎหมายวิธีพิจารณาความแพ่ง",
    "ประมวลกฎหมายที่ดิน", "ประมวลรัษฎากร", "พระธรรมนูญศาลยุติธรรม",
]


def load_file_words(path: Path) -> set[str]:
    words = set()
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w and not w.startswith("#"):
                    words.add(w)
    return words


def append_words(path: Path, new_words: list[str]) -> int:
    existing = load_file_words(path)
    to_add = [w for w in new_words if w not in existing and THAI_ONLY_RE.match(w) and len(w) >= 2]
    if not to_add:
        return 0

    with open(path, "a", encoding="utf-8") as f:
        for w in to_add:
            f.write(f"{w}\n")
    return len(to_add)


def harvest_countries():
    print(f"Downloading countries from {COUNTRIES_URL}...")
    req = urllib.request.Request(COUNTRIES_URL, headers={"User-Agent": "ThaiBreakBot/1.0"})
    with urllib.request.urlopen(req) as resp:
        text = resp.read().decode("utf-8")

    countries = []
    for line in text.splitlines():
        c = line.strip()
        if c and THAI_ONLY_RE.match(c):
            countries.append(c)

    target_path = DATA_DIR / "proper-names" / "countries.txt"
    added = append_words(target_path, countries)
    print(f"✓ Countries: added {added} new country names to {target_path.relative_to(ROOT_DIR)}")


def harvest_legal():
    target_path = DATA_DIR / "domains" / "legal.txt"
    added = append_words(target_path, LEGAL_TERMS)
    print(f"✓ Legal: added {added} terminology items to {target_path.relative_to(ROOT_DIR)}")


def main():
    print("--- Harvesting Open Datasets (CC0 & Public Domain) ---")
    harvest_countries()
    harvest_legal()
    print("✓ Harvest completed. Run scripts/format.py and scripts/validate.py next.")


if __name__ == "__main__":
    main()
