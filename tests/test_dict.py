#!/usr/bin/env python3
"""
Unit tests for thai-break-dict-extra scripts.
"""

import tempfile
import unittest
from pathlib import Path

# Add scripts directory to sys.path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from format import clean_and_format_file
from validate import thai_spelling_problem, validate_file
from build import load_words_from_file, thai_sort_key


class TestDictScripts(unittest.TestCase):

    def test_thai_sort_key(self):
        # Leading vowels (เ แ โ ใ ไ) should be sorted based on following consonant
        self.assertEqual(thai_sort_key("เก"), "กเ")
        self.assertEqual(thai_sort_key("กบ"), "กบ")
        self.assertEqual(thai_sort_key("โคน"), "คโน")

    def test_validate_and_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"

            # Create an unformatted file with BOM, CRLF, duplicates, blank line, and unsorted words
            content = "\ufeffปลา\r\n\r\nกบ\r\nกบ\r\nหมู   \r\nไก่\r\n"
            test_file.write_bytes(content.encode("utf-8"))

            # Validate should catch multiple errors
            errors = validate_file(test_file)
            self.assertTrue(len(errors) > 0)

            # Format the file
            original_lines, formatted_count = clean_and_format_file(test_file)
            self.assertEqual(formatted_count, 4)  # กบ, ไก่, ปลา, หมู (unique: 4)

            # Validate again - should have 0 errors now
            errors_after = validate_file(test_file)
            self.assertEqual(errors_after, [])

    def test_thai_spelling_problem(self):
        for word in ["กระท\u0e4d\u0e32", "น\u0e4d\u0e49\u0e32", "การเเสดง", "\u0e38โพสต์",
                     "จ\u0e31\u0e31มป์", "ล\u0e47\u0e47อก", "อนุสรณ\u0e4c\u0e4c",
                     "จักรพันธ\u0e4c\u0e38", "น\u0e33\u0e49"]:
            self.assertIsNotNone(thai_spelling_problem(word), word)
        # canonical words and intentional elongations in misspellings/ pass
        for word in ["กระทำ", "น้ำ", "การแสดง", "จักรพันธุ์", "ค่าา", "จ้าาา", "ณัฐ"]:
            self.assertIsNone(thai_spelling_problem(word), word)

    def test_load_words(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "sample.txt"
            test_file.write_text("# Comment\nคำที่หนึ่ง\nคำที่สอง\n# Another comment\n", encoding="utf-8")

            words = load_words_from_file(test_file)
            self.assertEqual(words, {"คำที่หนึ่ง", "คำที่สอง"})


if __name__ == "__main__":
    unittest.main()
