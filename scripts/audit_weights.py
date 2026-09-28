#!/usr/bin/env python3
"""
scripts/audit_weights.py
Audit tier weights and artifact consistency (no licensed corpus needed).

Checks (FAIL = exit 1, CI-usable):
  1. TSV hygiene: every line is `word<TAB>weight`, weight is finite and > 0.
  2. Guardrails hold IN THE ARTIFACT (independent re-implementation):
     - base-dict words with len <= 4 must be 1.0 (homograph guardrail)
     - words with len <= 3 and no dot must be <= 1.5 (short-word guardrail)
  3. Artifact consistency: the word SETS of dist .txt / .tsv / .dawg
     (TBD1 minimal DAWG parsed with stdlib only) must be identical.

Report-only (never fails):
  4. Weight distribution per band + top-weight words per category.
  5. Empirical weight-parity probes: segment fixed sample sentences with the
     PHP engine twice over the SAME word set — tier-weighted (TSV) vs
     uniform (TXT) — and report divergences. DAWG binaries store no weights,
     so Go/TS/PHP-DAWG paths are uniform by format design.
     NOTE (measured 2026-09-28): 0/10 probes, 0/2000 random extra-pairs and
     0/300 ambiguous strings diverge — under -log unigram costs, word COUNT
     dominates partitions, the length bonus aligns weight-order with
     length-order, and guardrails pin the short high-tier words that could
     flip outcomes. Tier weights are nearly behaviorally inert on this
     engine; segmentation quality comes from the word SET (curation).

Usage:
  python3 scripts/audit_weights.py [--skip-php]
"""

import math
import struct
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "data"
BASE_DICT = ROOT.parent / "thai-break" / "data" / "words.txt"
TSV = ROOT / "dist" / "words-extra.tsv"
TXT = ROOT / "dist" / "words-extra.txt"
DAWG = ROOT / "dist" / "words-extra.dawg"
PHP_AUTOLOAD = ROOT.parent / "thai-break" / "vendor" / "autoload.php"

SKIP_PHP = "--skip-php" in sys.argv

# Sample sentences exercising tier weights, guardrails and slang.
PROBE_SENTENCES = [
    "ความมั่นคงทดลองเผยแพร่สะพาน",
    "จังหวัดเลยตากแพร่ฝนตกหนัก",
    "กรุงเทพมหานครดำเนินการเสียชีวิตที่เกิดเหตุ",
    "กฏจราจรเว็ปไซต์หมูกะทะอร่อย",
    "ไปกินกันไม่ชอบสวยกว่าด้วยครับ",
    "งื้อออถถถว้าววววอยากกก",
    "สวัสดีครับคุณลูกค้ายินดีต้อนรับ",
    "รถไฟฟ้าสถานีสยามถนนสีลม",
    "กระทรวงดิจิทัลเพื่อเศรษฐกิจและสังคม",
    "มหาวิทยาลัยเชียงใหม่โรงพยาบาลศิริราช",
]


def load_words(path: Path) -> set[str]:
    words = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            w = line.strip()
            if w and not w.startswith("#"):
                words.add(w)
    return words


def load_tsv(path: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    errors: list[str] = []
    with open(path, encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 2:
                errors.append(f"Line {idx}: not word<TAB>weight")
                continue
            word, raw = parts[0].strip(), parts[1].strip()
            try:
                w = float(raw)
            except ValueError:
                errors.append(f"Line {idx}: bad weight {raw!r}")
                continue
            if not math.isfinite(w) or w <= 0:
                errors.append(f"Line {idx}: non-positive weight {raw!r}")
                continue
            if word in out:
                errors.append(f"Line {idx}: duplicate {word!r}")
            out[word] = w
    return out, errors


def load_dawg_words(path: Path) -> set[str]:
    """Minimal TBD1 reader (see build.py::build_dawg_from_words)."""
    buf = path.read_bytes()
    assert buf[:4] == b"TBD1", "bad magic"
    num_states, num_words = struct.unpack_from("<II", buf, 4)
    states: list[tuple[bool, list[tuple[int, int]]]] = []
    off = 12
    for _ in range(num_states):
        head = buf[off]
        off += 1
        is_final = bool(head & 0x80)
        n_edges = head & 0x7F
        edges = []
        for _ in range(n_edges):
            ch, child = struct.unpack_from("<HH", buf, off)
            off += 4
            edges.append((ch, child))
        states.append((is_final, edges))
    words: set[str] = set()

    def walk(sid: int, prefix: str) -> None:
        is_final, edges = states[sid]
        if is_final:
            words.add(prefix)
        for ch, child in edges:
            walk(child, prefix + chr(ch))

    walk(0, "")
    assert len(words) == num_words, f"DAWG word count {len(words)} != header {num_words}"
    return words


def php_segment(sentences: list[str], weighted: bool) -> list[str] | None:
    """Segment via PHP engine over base+extra with tier weights (TSV) or not.

    Builds a merged temp dict in Python (DictionaryLoader::merge is a stub)
    and shells out to tools/segment.php, which picks fromTsvFile for .tsv
    (weighted) and fromTextFile for .txt (uniform 1.0).
    """
    import tempfile

    if not PHP_AUTOLOAD.exists():
        print("[skip] PHP vendor autoload not found; parity demo skipped")
        return None
    base = load_words(BASE_DICT)
    tsv, _ = load_tsv(TSV)
    merged: dict[str, float] = {w: 1.0 for w in base}
    merged.update(tsv)
    suffix = ".tsv" if weighted else ".txt"
    try:
        with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False,
                                          encoding="utf-8") as tmp:
            if weighted:
                tmp.write("".join(f"{w}\t{wt:.2f}\n" for w, wt in merged.items()))
            else:
                tmp.write("\n".join(merged) + "\n")
            dict_path = tmp.name
        seg = ROOT.parent / "thai-break" / "tools" / "segment.php"
        res = subprocess.run(
            ["php", str(seg), dict_path],
            input="\n".join(sentences) + "\n",
            capture_output=True, text=True, timeout=300,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"[skip] PHP harness failed ({e}); parity demo skipped")
        return None
    finally:
        try:
            Path(dict_path).unlink()
        except (NameError, FileNotFoundError):
            pass
    if res.returncode != 0:
        print(f"[skip] PHP harness error: {res.stderr.strip()[:300]}")
        return None
    return res.stdout.split("\n")[: len(sentences)]


def main() -> int:
    failures: list[str] = []

    tsv, tsv_errors = load_tsv(TSV)
    if tsv_errors:
        failures.append(f"TSV hygiene: {len(tsv_errors)} errors")
        for e in tsv_errors[:10]:
            print(f"  ❌ {e}")
    else:
        print(f"✓ TSV hygiene: {len(tsv):,} entries, all finite positive weights")

    base = load_words(BASE_DICT)
    guard1 = [w for w, wt in tsv.items() if w in base and len(w) <= 4 and wt != 1.0]
    guard2 = [w for w, wt in tsv.items() if "." not in w and len(w) <= 3 and wt > 1.5]
    if guard1:
        failures.append(f"homograph guardrail: {len(guard1)} escapes: {guard1[:10]}")
    else:
        print("✓ homograph guardrail: all base words len<=4 pinned at 1.0")
    if guard2:
        failures.append(f"short-word guardrail: {len(guard2)} escapes: {guard2[:10]}")
    else:
        print("✓ short-word guardrail: all dotless words len<=3 capped at 1.5")

    txt_words = load_words(TXT)
    dawg_words = load_dawg_words(DAWG)
    for name, s in (("txt", txt_words), ("tsv", set(tsv)), ("dawg", dawg_words)):
        print(f"  • {name}: {len(s):,} words")
    if txt_words == set(tsv) == dawg_words:
        print("✓ artifact consistency: txt/tsv/dawg word sets identical")
    else:
        only_txt = txt_words - set(tsv) - dawg_words
        only_tsv = set(tsv) - txt_words - dawg_words
        only_dawg = dawg_words - txt_words - set(tsv)
        failures.append(
            f"artifact mismatch: only-txt={len(only_txt)} only-tsv={len(only_tsv)} only-dawg={len(only_dawg)}")
        print(f"  ❌ only-txt: {sorted(only_txt)[:5]}")
        print(f"  ❌ only-tsv: {sorted(only_tsv)[:5]}")
        print(f"  ❌ only-dawg: {sorted(only_dawg)[:5]}")

    bands = Counter()
    for wt in tsv.values():
        bands["w>=5" if wt >= 5 else "2<=w<5" if wt >= 2 else "1<w<2" if wt > 1 else "w==1" if wt == 1 else "w<1"] += 1
    print(f"\n--- weight distribution ---\n  {dict(sorted(bands.items()))}")
    top = sorted(tsv.items(), key=lambda kv: -kv[1])[:8]
    print(f"  top weights: {[(w, f'{wt:.2f}') for w, wt in top]}")

    if not SKIP_PHP:
        a = php_segment(PROBE_SENTENCES, True)
        b = php_segment(PROBE_SENTENCES, False)
        if a is not None and b is not None:
            divs = [(s, x, y) for s, x, y in zip(PROBE_SENTENCES, a, b) if x != y]
            print(f"\n--- weight-parity probes (PHP: TSV-weighted vs TXT-uniform, "
                  f"{len(PROBE_SENTENCES)} probes) ---")
            print(f"  divergences: {len(divs)}/{len(PROBE_SENTENCES)}")
            for s, x, y in divs:
                print(f"  in : {s}\n  tsv: {x}\n  txt: {y}")
            if not divs:
                print("  (expected: tier weights rarely flip -log Viterbi outcomes; "
                      "see module docstring)")
    else:
        print("\n[skip] parity demo (--skip-php)")

    print("\n" + "=" * 50)
    if failures:
        print(f"❌ AUDIT FAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("✅ weight audit passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
