# thai-break-dict-extra

[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](http://creativecommons.org/publicdomain/zero/1.0/)

คลังคำศัพท์พิเศษเสริม (Pluggable / Supplementary Thai Dictionary) สำหรับเพิ่มความแม่นยำในการตัดคำภาษาไทย (Thai Word Tokenization / Segmentation) ให้แก่ระบบตัดคำ เช่น **[thai-break](https://github.com/kamthorn/thai-break)**, **thai-break-service**, หรือ Tokenizer อื่น ๆ

โปรเจกต์นี้ออกแบบมาเพื่อทำหน้าที่เป็น **พจนานุกรมเสริม (Extra Dictionary)** แยกต่างหากจากพจนานุกรมพื้นฐาน (Base Dictionary) โดยรวบรวมกลุ่มคำเฉพาะทางที่มัก **ไม่ปรากฏในพจนานุกรมทั่วไป** หรือคำที่มักจะถูกตัดเป็นชิ้นเล็กชิ้นน้อยผิดความหมาย เพื่อให้ผู้ใช้สามารถเลือกดึงเฉพาะหมวดหมู่ที่ต้องการไปเสริมคุณภาพได้ตาม Use Case

🌐 **ลองใช้งานในเบราว์เซอร์:** [thai-break-demo](https://kamthorn.github.io/thai-break-demo/) เลือกใช้พจนานุกรมชุดนี้ตัดคำและเทียบผลกับพจนานุกรมพื้นฐานได้ ([ซอร์สโค้ด](https://github.com/kamthorn/thai-break-demo))

---

## 📁 โครงสร้างหมวดหมู่คำศัพท์ (`data/`)

จัดหมวดหมู่แบบแยกโฟลเดอร์ 15 หมวดหมู่ รวม 40 ไฟล์คำศัพท์ (28,184 คำหลังรวมและตัดซ้ำ):

```text
data/
├── proper-names/             # ชื่อเฉพาะ (Proper Names / Named Entities)
│   ├── provinces.txt         # รายชื่อ 77 จังหวัด และชื่อเรียกยอดนิยม (เช่น กรุงเทพฯ, อยุธยา, โคราช)
│   ├── districts.txt         # อำเภอ, เขต, แขวง, ตำบล, แหล่งท่องเที่ยวสำคัญ
│   ├── subdistricts.txt        # ตำบล/แขวงทั่วประเทศ (สกัดจาก thailand-geography-json, MIT)
│   ├── countries.txt         # ชื่อประเทศ, ดินแดน และเมืองสำคัญทั่วโลก (ภาษาไทย)
│   ├── organizations.txt     # หน่วยงานราชการ, กระทรวง, กรม, องค์กรสากล, ธนาคาร
│   ├── brands.txt            # แบรนด์สินค้า, บริษัท, แพลตฟอร์มโซเชียล, ห้างสรรพสินค้า
│   ├── persons.txt           # ชื่อบุคคลสำคัญ, บุคคลสาธารณะ (ชื่อ-นามสกุลเต็ม)
│   ├── given-names.txt       # ชื่อตัวคนไทยทั่วไป (PyThaiNLP CC0/Apache-2.0, คัดกรองด้วย LST20)
│   └── landmarks.txt         # โบราณสถาน, วัดสำคัญ, แหล่งท่องเที่ยว, สถานที่ราชการสำคัญ
│
├── news/                     # ภาษาข่าวและสื่อสารมวลชน (คำประสมและคำเชื่อมที่พบบ่อยในสำนักข่าว)
│   ├── compounds.txt         # คำประสมกริยา/คำนามข่าว (ดำเนินการ, เสียชีวิต, ก่อเหตุ, ที่เกิดเหตุ)
│   ├── connectives.txt       # คำเชื่อมและสำนวนบอกกาล/เงื่อนไข (ดังกล่าว, เนื่องจาก, อย่างไรก็ตาม)
│   └── royal.txt             # คำราชาศัพท์และพระนามในข่าวพระราชสำนัก
│
├── abbreviations/            # คำย่อและอักษรย่อที่ใช้บ่อย
│   ├── common.txt            # คำย่อทั่วไป ทั้งแบบมีจุดและไม่มีจุด
│   ├── months.txt            # ชื่อย่อ 12 เดือนแบบมีจุด (ม.ค. - ธ.ค., weight 7.0)
│   ├── months-dotless.txt    # ชื่อย่อเดือนไร้จุด (มค มีค ตค, weight 0.5: ตัดวันที่ได้ แต่แพ้คำทั่วไปเสมอ)
│   ├── ranks.txt             # ยศทหาร ตำรวจ และตำแหน่งบริหาร (พ.ต.อ., ผบ.ตร., รมว.)
│   ├── titles.txt            # คำนำหน้านามและฐานันดรศักดิ์ (น.ส., ด.ช., ด.ญ., ม.ร.ว.)
│   ├── addresses.txt         # คำย่อที่อยู่/สถานที่ (จ., อ., ต., ถ., ซ., กม., สน., สภ.)
│   └── units.txt             # คำย่อหน่วยวัด (กก., มก., กม., ลบ.ม., ตร.ม.)
│
├── politics/                 # การเมือง สังคม และนโยบาย
│   ├── parties.txt           # พรรคการเมืองในประวัติศาสตร์และปัจจุบัน
│   └── society.txt           # สิทธิมนุษยชน, รัฐสวัสดิการ, สมรสเท่าเทียม, กฎหมายและรัฐธรรมนูญ
│
├── transit/                  # คมนาคม ระบบขนส่งมวลชน และโครงสร้างพื้นฐาน
│   ├── stations.txt          # สถานีรถไฟฟ้า BTS, MRT, ARL, SRT, รถไฟชานเมือง, ท่าเรือ
│   └── roads.txt             # ถนนสายหลัก, สะพานข้ามแม่น้ำ, ทางด่วน, มอเตอร์เวย์
│
├── education/                # สถาบันการศึกษา
│   ├── universities.txt      # มหาวิทยาลัย และสถาบันอุดมศึกษา (ทั้งชื่อเต็มและชื่อเรียกทั่วไป)
│   └── schools.txt           # โรงเรียนมัธยมและประถมชื่อดัง
│
├── automotive/               # ยานยนต์และเทคโนโลยีพลังงานใหม่
│   └── vehicles.txt          # ศัพท์รถยนต์ EV, ไฮบริด, ยี่ห้อ และรุ่นรถยอดนิยมในไทย
│
├── culture/                  # ประเพณี วัฒนธรรม และความเชื่อ
│   ├── beliefs.txt           # สายมู, วัตถุมงคล, สิ่งศักดิ์สิทธิ์, พระเครื่อง, โหราศาสตร์
│   └── traditions.txt        # ประเพณี, เทศกาล, พิธีกรรมไทย, วันสำคัญ
│
├── pop-culture/              # ป็อปคัลเจอร์ เกม และอนิเมะ
│   ├── gaming.txt            # ศัพท์เกมมิ่ง, สตรีมเมอร์, อีสปอร์ต, ประเภทตัวละคร
│   └── anime-manga.txt       # ศัพท์อนิเมะ, มังงะ, ไลท์โนเวล, วงการไอดอล
│
├── environment/              # สิ่งแวดล้อมและความยั่งยืน (ESG)
│   └── esg.txt               # คาร์บอนเครดิต, พลังงานสะอาด, โซลาร์เซลล์, ปัญหาฝุ่นละออง
│
├── general/                  # ศัพท์ทั่วไปเพิ่มเติม (Tier 3.5, weight 2.0)
│   └── thai2fit.txt          # ศัพท์ภาษาไทยทั่วไปจาก Thai2fit (PyThaiNLP, CC0-1.0)
│
├── loanwords/                # คำทับศัพท์ / คำยืมภาษาต่างประเทศ
│   ├── tech.txt              # ศัพท์คอมพิวเตอร์, เทคโนโลยี, ซอฟต์แวร์, AI
│   ├── food.txt              # อาหาร, ขนม, เครื่องดื่ม, ชา, กาแฟ
│   └── general.txt           # คำทับศัพท์ทั่วไป, กิจกรรม, ไลฟ์สไตล์, แฟชั่น
│
├── misspellings/             # คำที่มักสะกดผิดบ่อย (Common Misspellings)
│   └── common.txt            # คำเขียนผิดที่พบบ่อย (ช่วยให้ตัดกลุ่มคำได้เป็นก้อน ไม่แตกกระจาย)
│
├── slang/                    # คำสแลง / ภาษาปาก / ศัพท์อินเทอร์เน็ต
│   └── internet.txt          # คำฮิตติดเทรนด์โซเชียลมีเดีย, ศัพท์วัยรุ่น
│
└── domains/                  # ศัพท์เฉพาะทางตามสาขาวิชาชีพ
    ├── medical.txt           # การแพทย์, สาธารณสุข, ชื่อโรค, ยา, อาการ
    ├── finance.txt           # การเงิน, หุ้น, คริปโทเคอร์เรนซี, บัญชี, ภาษี
    └── legal.txt             # กฎหมาย, การดำเนินคดี, นิติกรรม, ศาล
```

---

## 🛠️ เครื่องมือและสคริปต์ (`scripts/`)

ทุกสคริปต์พัฒนาด้วย **Python 3 Standard Library** โดยไม่ต้องติดตั้ง dependencies ภายนอก

### 1. การจัดรูปแบบไฟล์อัตโนมัติ (`format.py`)
ทำความสะอาดข้อมูล ตัดช่องว่าง/อักขระล่องหน (Zero-width space, BOM), กรองคำซ้ำในไฟล์ และเรียงลำดับ (Sort) ให้อัตโนมัติ:
```bash
python3 scripts/format.py
```

### 2. การตรวจสอบความถูกต้อง (`validate.py`)
ตรวจสอบความสมบูรณ์ของข้อมูล (ใช้สำหรับ CI / Pre-commit hook):
- การเข้ารหัสแบบ **UTF-8 (No BOM)**
- การขึ้นบรรทัดใหม่แบบ Unix (`\n` เท่านั้น ไม่มี `\r`)
- ไม่มีบรรทัดว่างและไม่มีช่องว่างหน้า/หลังคำ
- คำในแต่ละไฟล์ต้องจัดเรียงลำดับตามตัวอักษรอย่างถูกต้อง
- แจ้งเตือนกรณีพบคำซ้ำข้ามหมวดหมู่
```bash
python3 scripts/validate.py
```

### 3. การรวมคำศัพท์และการสร้างพจนานุกรม (`build.py`)
รวบรวมคำศัพท์จากหมวดหมู่ที่ต้องการ คำนวณค่าน้ำหนักตาม Tier หมวดหมู่ และส่งออกเป็น 4 รูปแบบพร้อมกันใน `dist/` (พร้อมชุด Lines preset ที่สร้างอัตโนมัติ):
- `dist/words-extra.txt`: รายการคำเรียงตามตัวอักษร (1 คำต่อบรรทัด, 28,184 คำ)
- `dist/words-extra.tsv`: คำศัพท์พร้อมค่าน้ำหนักภาษาศาสตร์ (Tier Weights 0.5 - 8.0)
- `dist/words-extra.dawg`: พจนานุกรมไบนารีคอมแพกต์ Minimal DAWG (~271 KB) สำหรับ Go, TypeScript, PHP
- `dist/words-extra.fst`: พจนานุกรมไบนารี Finite State Transducer (~688 KB) สำหรับ Rust, C/C++, Python (C-FFI) รองรับ zero-copy mmap
- `dist/words-extra-lines.{txt,tsv,dawg,fst}`: ชุดคำสำหรับโหมดจัดบรรทัด (ตัดชื่อเฉพาะ/โรงเรียน/คำประสมข่าวออก, 9,218 คำ) สร้างอัตโนมัติเมื่อ build แบบ default

```bash
# 1. รวมคำศัพท์พิเศษทั้งหมดพร้อมคำนวณค่าน้ำหนัก (ค่าเริ่มต้น)
python3 scripts/build.py

# 2. เลือกเฉพาะบางหมวดหมู่ (Modular Build ด้วย --include)
python3 scripts/build.py --include transit,automotive,proper-names --output dist/words-transit.txt

# 3. กำหนดโหมดน้ำหนัก (tier / uniform)
python3 scripts/build.py --weights-mode tier

# 4. ทดสอบเปรียบเทียบกับ Base Dictionary (Optional)
python3 scripts/build.py --base-dict ../thai-break/data/words.txt
```

### 4. การสกัดข้อมูลเปิดสาธารณะ (Open Data Harvesters)

โปรเจกต์นี้มีสคริปต์สกัดคำศัพท์จากแหล่งข้อมูลสาธารณะที่ถูกกฎหมายลิขสิทธิ์ 100%:

```bash
# สกัดจังหวัด/อำเภอ/ตำบลทางการทั่วประเทศ จากข้อมูลเปิด thailand-geography-json (MIT)
# -> data/proper-names/{provinces,districts,subdistricts}.txt
python3 scripts/harvest_geodata.py

# สกัดชื่อเฉพาะ มหาวิทยาลัย โรงเรียน ทางหลวง องค์กร จากฐานข้อมูลเปิดของวิกิพีเดียไทย (CC BY-SA 4.0)
python3 scripts/harvest_wikipedia_titles.py

# สกัดชื่อประเทศ คำทับศัพท์ และศัพท์กฎหมาย จาก PyThaiNLP corpus (CC0-1.0) และประมวลกฎหมาย (Public Domain)
# -> data/proper-names/countries.txt, data/loanwords/*.txt, data/domains/legal.txt
python3 scripts/harvest_pythainlp_cc0.py

# สกัดชื่อตัวคนไทยจาก PyThaiNLP (CC0/Apache-2.0) คัดเฉพาะชื่อที่ไม่ชนกับวลีธรรมดา
# (ตรวจด้วยความถี่ใน LST20 นอกช่วงชื่อคน — ใช้แค่ตัดสินใจว่าเก็บคำไหน ไม่คัดลอกข้อความ LST20 ลง data/)
# -> data/proper-names/given-names.txt
python3 scripts/harvest_given_names.py [--lst20 ../LST20_Corpus]

# สกัดคำสแลง/ศัพท์โซเชียลจาก Wisesight Sentiment (CC0-1.0) และคำใหม่จาก Thai2fit (CC0-1.0)
# -> data/slang/internet_new.txt (ไฟล์พักรอตรวจทานด้วยคนก่อน merge ทุกครั้ง)
python3 scripts/harvest_wisesight_vocab.py

# กลั่นกรองผล harvest: คำสั้น Wisesight -> slang/internet.txt, คำทั่วไป Thai2fit -> general/thai2fit.txt
# (คำลากเสียง/เสียงหัวเราะ เช่น งื้อออ ถถถ จะถูกย้ายไป misspellings/common.txt อัตโนมัติ)
python3 scripts/curate_harvest.py [--dry-run]

# สกัด bigram จากตัวอย่างที่คนตัดคำไว้แล้วใน Wisesight (CC0-1.0, human-tokenized)
# -> data/bigrams-wisesight.tsv (commit ได้ ปลอดภัยลิขสิทธิ์)
# ส่วน bigram จาก LST20 ให้ใช้ scripts/harvest_bigrams_lst20.py ซึ่งเขียนลง local/ เท่านั้น
python3 scripts/harvest_bigrams_wisesight.py [--min-count 2]

# สกัด bigram คุณภาพสูงจากคลังข่าว Prachathai-67k (Apache-2.0, 54,380 บทความ)
# -> data/bigrams-prachathai.tsv (955,967 คู่คำ; commit ได้ ปลอดภัยลิขสิทธิ์)
# ใช้ segmenter ของ ThaiBreak ตัดคำแล้วนับคู่คำติดกัน (bootstrapping)
python3 scripts/harvest_bigrams_prachathai.py [--min-count 5]
```

> [!NOTE]
> `data/slang/internet_new.txt` เป็นไฟล์พักชั่วคราวสำหรับตรวจทาน **ห้าม merge เข้า build โดยตรง**
> (build.py จะหยิบ `.txt` ทุกไฟล์ใน `data/` ไปรวม) — ตรวจทานแล้วลบทิ้งหลัง curate เสมอ

### 5. วัดความแม่นยำการตัดคำ (`benchmark.py`)

วัดผลกับคลังข้อมูลที่ตัดคำไว้แล้ว (Gold Corpus) ได้ทั้ง LST20 และ Blackboard Treebank รายงาน Word P/R/F1 (ตำแหน่งคำตรงกันทั้งคำ), Boundary P/R/F1 และแยกสาเหตุของคำที่ตัดผิด (ไม่มีในพจนานุกรม / มีแต่ตัดผิด / ไม่ใช่อักษรไทย) ข้อความถูกแบ่งเป็นท่อนที่ช่องว่างและขอบเขตประโยค และไม่นับช่องว่างในการให้คะแนน

```bash
# ThaiBreak (Python binding ของ ../thai-break) บน LST20 eval
python3 scripts/benchmark.py --corpus lst20 --corpus-dir ../LST20_Corpus/eval \
    --dict ../thai-break/data/words.txt

# เพิ่มคำจาก dist/words-extra.txt และใช้ตัวตัดคำใดก็ได้ที่อ่านข้อความทีละบรรทัดจาก stdin
# แล้วพิมพ์คำคั่นด้วย "|" ({dict} จะถูกแทนด้วยพจนานุกรมที่รวมแล้ว)
python3 scripts/benchmark.py --corpus lst20 --corpus-dir ../LST20_Corpus/eval \
    --dict ../thai-break/data/words.txt --dict dist/words-extra.txt \
    --segmenter-cmd "php ../thai-break/tools/segment.php {dict}"

# Blackboard Treebank ระดับคำย่อย (แยกที่ "|") โดยตัดประโยคที่ซ้ำกับ LST20 train ออก
python3 scripts/benchmark.py --corpus blackboard --corpus-dir ../Corpus-BlackboardTreebank/thai10_conll \
    --subword --exclude-overlap ../LST20_Corpus/train --dict ../thai-break/data/words.txt
```

ใช้ train/eval ในการปรับแต่ง และรายงานผลบน test เฉพาะผลสุดท้ายเท่านั้น

### 6. นับคำจากคลังข้อมูลเพื่อทดลอง (`extract_vocab.py`)

```bash
python3 scripts/extract_vocab.py --corpus lst20 --corpus-dir ../LST20_Corpus/train \
    --base-dict ../thai-break/data/words.txt
# -> local/lst20-train-vocab.tsv, local/lst20-train-new-words.tsv
```

ไฟล์ที่ได้อยู่ใน `local/` ซึ่งถูก gitignore ไว้ ใช้ทดสอบเท่านั้น

> [!IMPORTANT]
> **คลังข้อมูลไม่ได้อยู่ใน repository นี้และห้ามนำเข้ามา**
> - **LST20 (NECTEC):** ใช้ได้ฟรีสำหรับงานวิจัย งานไม่ใช่เชิงพาณิชย์ และโครงการโอเพนซอร์ส (โปรดอ้างอิงรายงานเทคนิค) ห้ามแก้ไขหรือแจกจ่ายข้อมูล การใช้เชิงพาณิชย์ต้องได้รับอนุญาต ดู `AGREEMENT.txt` ของคลังข้อมูล
> - **Blackboard Treebank:** ข้อความมาจากแหล่งข่าวเดียวกับ LST20 ให้ถือเงื่อนไขเดียวกันจนกว่าจะตรวจสอบ license ของต้นทาง
> - รายการคำและค่าความถี่ที่ได้จากคลังข้อมูลเหล่านี้ใช้ทดสอบใน `local/` เท่านั้น ห้ามรวมเข้า `data/` หรือ `dist/` จนกว่าจะได้รับอนุญาตจากเจ้าของคลังข้อมูล

---

### 7. การกลั่นกรองคำศัพท์และตรวจสอบน้ำหนัก (`curate_thai2fit.py`, `audit_weights.py`)

```bash
# กลั่นกรอง general/thai2fit.txt: ย้ายคำสะกดผิด -> misspellings (0.5),
# ลบวลีไวยากรณ์ (ไปกินกัน, ไม่ชอบ) ที่ประกอบจาก base ได้, ย้ายคำหยาบ -> slang
# (กฎวลี: แยกเป็นคำ base ได้ >= 2 คำ มี function word และไม่ปรากฏใน words_th (CC0))
python3 scripts/curate_thai2fit.py --dry-run   # ทบทวนก่อน
python3 scripts/curate_thai2fit.py             # ประยุกต์ใช้

# ตรวจสุขอนามัย TSV, guardrails ใน artifact, ความตรงกันของ txt/tsv/dawg,
# และ parity probe (weighted TSV vs uniform TXT ผ่าน PHP engine)
python3 scripts/audit_weights.py [--skip-php]
```

> [!NOTE]
> ภายใต้ต้นทุน unigram แบบ `-log(weight/total)` จำนวนคำในเส้นทางมีอิทธิพลเหนือน้ำหนักมาก
> (วัดจริง: weighted vs uniform ให้ผลตรงกัน 10/10 probes, 2000/2000 คู่สุ่ม, 300/300 ข้อความกำกวม)
> คุณภาพการตัดคำจึงขึ้นกับ **ชุดคำ (curation)** เป็นหลัก ไม่ใช่น้ำหนัก — DAWG ไม่เก็บน้ำหนักอยู่แล้วโดยออกแบบ

## 🧪 การรันชุดทดสอบ (Unit Tests)

```bash
python3 -m unittest discover tests
```

---

## 🤝 แนวทางการเพิ่มคำศัพท์ (Contribution Guidelines)

1. เลือกโฟลเดอร์/ไฟล์ใน `data/` ให้ตรงกับหมวดหมู่ของคำ
2. บันทึกคำศัพท์ **1 คำ ต่อ 1 บรรทัด**
3. รันคำสั่งฟอร์แมตและตรวจสอบก่อน Commit:
   ```bash
   python3 scripts/format.py
   python3 scripts/validate.py
   python3 scripts/build.py
   ```

---

---

## 📚 ที่มาของข้อมูลและสัญญาอนุญาต (Data Sources & Licenses)

| แหล่งข้อมูล | ใช้ทำอะไร | สัญญาอนุญาต | การอ้างอิง |
|---|---|---|---|
| PyThaiNLP `words_th_thai2fit_201810.txt` | `general/thai2fit.txt` | CC0-1.0 | PyThaiNLP `corpus_license.md` |
| Wisesight Sentiment (26,737 ข้อความโซเชียล) | `slang/internet.txt` (รอบท review) | CC0-1.0 | Suriyawongkul et al., Zenodo 10.5281/zenodo.3457446 |
| Wisesight word-tokenization (1,153 ประโยคคนตัด) | `data/bigrams-wisesight.tsv` (3,868 คู่) | CC0-1.0 | โฟลเดอร์ word-tokenization ใน repo เดียวกัน |
| Prachathai-67k (54,380 บทความข่าว) | `data/bigrams-prachathai.tsv` (955,967 คู่คำ) | Apache-2.0 | wannaphong/prachathai67k (HuggingFace) |
| PyThaiNLP `countries_th.txt`, `th_en_transliteration` | `proper-names/countries.txt`, `loanwords/*.txt` | CC0-1.0 | PyThaiNLP `corpus_license.md` |
| thailand-geography-json (Joe Takara) | `proper-names/{provinces,districts,subdistricts}.txt` | MIT © 2023-Present Joe Takara | https://github.com/thailand-geography-data/thailand-geography-json |
| วิกิพีเดียภาษาไทย | ชื่อเฉพาะ/องค์กร/สถานที่ | CC BY-SA 4.0 | ลิงก์บทความต้นทาง |
| ประมวลกฎหมายไทย | `domains/legal.txt` | Public Domain (ม.7 พ.ร.บ.ลิขสิทธิ์) | — |
| LST20 / Blackboard Treebank | ทดสอบใน `local/` และสกัดสถิติ bigram ไว้ใช้ภายในเท่านั้น | NECTEC Data Agreement — **ห้าม commit ลง `data/`/`dist/`** จนกว่าเจ้าของจะอนุญาต | อ้างอิง technical report ของ NECTEC เมื่อใช้งาน |

## 📜 สัญญาอนุญาต (License)

โปรเจกต์นี้และคลังคำศัพท์ทั้งหมดเผยแพร่ภายใต้สัญญาอนุญาต **[Creative Commons Zero 1.0 Universal (CC0 1.0)](LICENSE)** — Public Domain Dedication

ทุกคนสามารถนำข้อมูลคำศัพท์และเครื่องมือในคลังนี้ไปใช้งาน ทำซ้ำ ดัดแปลง รวมเข้ากับซอฟต์แวร์อื่น หรือแจกจ่ายต่อได้อย่างเสรี ไม่ว่าจะเป็นงานเชิงพาณิชย์ (Commercial) หรือโครงการส่วนบุคคล โดยไม่มีข้อผูกมัดหรือเงื่อนไขทางกฎหมายใด ๆ
