# thai-break-dict-extra

คลังคำศัพท์พิเศษเสริม (Pluggable / Supplementary Thai Dictionary) สำหรับเพิ่มความแม่นยำในการตัดคำภาษาไทย (Thai Word Tokenization / Segmentation) ให้แก่ระบบตัดคำ เช่น **[thai-break](https://github.com/kamthorn/thai-break)**, **thai-break-service**, หรือ Tokenizer อื่น ๆ

โปรเจกต์นี้ออกแบบมาเพื่อทำหน้าที่เป็น **พจนานุกรมเสริม (Extra Dictionary)** แยกต่างหากจากพจนานุกรมพื้นฐาน (Base Dictionary) โดยรวบรวมกลุ่มคำเฉพาะทางที่มัก **ไม่ปรากฏในพจนานุกรมทั่วไป** หรือคำที่มักจะถูกตัดเป็นชิ้นเล็กชิ้นน้อยผิดความหมาย เพื่อให้ผู้ใช้สามารถเลือกดึงเฉพาะหมวดหมู่ที่ต้องการไปเสริมคุณภาพได้ตาม Use Case

---

## 📁 โครงสร้างหมวดหมู่คำศัพท์ (`data/`)

จัดหมวดหมู่แบบแยกโฟลเดอร์ 13 หมวดหมู่ รวม 26 ไฟล์คำศัพท์:

```text
data/
├── proper-names/             # ชื่อเฉพาะ (Proper Names / Named Entities)
│   ├── provinces.txt         # รายชื่อ 77 จังหวัด และชื่อเรียกยอดนิยม (เช่น กรุงเทพฯ, อยุธยา, โคราช)
│   ├── districts.txt         # อำเภอ, เขต, แขวง, ตำบล, แหล่งท่องเที่ยวสำคัญ
│   ├── countries.txt         # ชื่อประเทศ, ดินแดน และเมืองสำคัญทั่วโลก (ภาษาไทย)
│   ├── organizations.txt     # หน่วยงานราชการ, กระทรวง, กรม, องค์กรสากล, ธนาคาร
│   ├── brands.txt            # แบรนด์สินค้า, บริษัท, แพลตฟอร์มโซเชียล, ห้างสรรพสินค้า
│   ├── persons.txt           # ชื่อบุคคลสำคัญ, บุคคลสาธารณะ
│   └── landmarks.txt         # โบราณสถาน, วัดสำคัญ, แหล่งท่องเที่ยว, สถานที่ราชการสำคัญ
│
├── news/                     # ภาษาข่าวและสื่อสารมวลชน (จากคลังข่าวและ LST20)
│   ├── compounds.txt         # คำประสมกริยา/คำนามข่าว (ดำเนินการ, เสียชีวิต, ก่อเหตุ, ที่เกิดเหตุ)
│   ├── connectives.txt       # คำเชื่อมและสำนวนบอกกาล/เงื่อนไข (ดังกล่าว, เนื่องจาก, อย่างไรก็ตาม)
│   └── royal.txt             # คำราชาศัพท์และพระนามในข่าวพระราชสำนัก
│
├── abbreviations/            # คำย่อและอักษรย่อที่ใช้บ่อย
│   ├── common.txt            # คำย่อทั่วไป ทั้งแบบมีจุดและไม่มีจุด
│   ├── months.txt            # ชื่อย่อ 12 เดือน (ม.ค. - ธ.ค. และ มค - ธค)
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

### 3. การรวมคำศัพท์ (`build.py`)
รวบรวมคำศัพท์จากหมวดหมู่ที่ต้องการ กรองคำซ้ำ และส่งออกเป็นไฟล์เดียว:

```bash
# 1. รวมคำศัพท์พิเศษทั้งหมดเป็น dist/words-extra.txt (ค่าเริ่มต้น)
python3 scripts/build.py

# 2. เลือกเฉพาะบางหมวดหมู่ (Modular Build ด้วย --include)
# เช่น รวมเฉพาะหมวดคมนาคม ยานยนต์ และชื่อเฉพาะ
python3 scripts/build.py --include transit,automotive,proper-names --output dist/words-transit.txt

# 3. ยกเว้นบางหมวดหมู่ที่ไม่ต้องการ (ด้วย --exclude)
# เช่น ไม่ต้องการคำสะกดผิดและคำสแลง
python3 scripts/build.py --exclude misspellings,slang --output dist/words-formal.txt

# 4. ทดสอบเปรียบเทียบกับ Base Dictionary (Optional)
python3 scripts/build.py --base-dict ../thai-break-service/data/words.txt
```

### 4. วัดความแม่นยำการตัดคำ (`benchmark.py`)

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

### 5. นับคำจากคลังข้อมูลเพื่อทดลอง (`extract_vocab.py`)

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
