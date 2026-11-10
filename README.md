# BJT DC Bias Web App — ENG29 2121 Lab 02

Flask web application that computes the DC operating point of an NPN
Common-Emitter amplifier stage with **Voltage-Divider Bias**.

The Python backend does the math (this is not a static HTML page):
the browser form is submitted to Flask, which calls a separate
engineering module and renders the results.

## Circuit

```
        VCC
         |
     +---+---+
     |       |
    R1      RC      NPN Common Emitter
     |       |       (Voltage-Divider Bias)
     +----B  C
    R2     |
     |     E
    GND   RE
     |     |
     +--GND+
```

- `R1`: VCC → Base, `R2`: Base → GND (Thevenin source `VTH`, `RTH`)
- `RC`: VCC → Collector, `RE`: Emitter → GND

## Model assumptions

Forward-active approximation: constant β and constant VBE.

```
VTH = VCC · R2 / (R1 + R2)      RTH = R1·R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β+1)·RE)
IC  = β·IB                       IE  = (β+1)·IB
VE  = IE·RE                      VB  = VE + VBE
VC  = VCC − IC·RC                VCE = VC − VE
```

If `VTH ≤ VBE` the app reports **Cutoff**; if `VCE < 0.2 V` it reports
**Saturation** with a warning — in both cases the forward-active
approximation does not apply and the numbers are flagged, not trusted.

## Requirements

- Python 3.10+ (developed on 3.14; Windows `py` launcher works)
- Flask 3.x (the only dependency — see `requirements.txt`)

## Install

```powershell
# Windows (py launcher)
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```powershell
# Windows
.venv\Scripts\python.exe -m flask --app app run --debug
```

```bash
# Linux / macOS
flask --app app run --debug
```

Then open <http://127.0.0.1:5000/> in a browser. (Opening
`templates/index.html` directly will NOT work — the calculation
happens on the server.)

## Test

```powershell
# Windows
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

```bash
# Linux / macOS
python -m unittest discover -s tests -v
```

17 tests: 7 engineering-math cases in `tests/test_dc_bias.py` and 10
HTTP-route cases in `tests/test_web.py` (Flask test client), including
the live circuit-schematic value tests.

## Inputs and outputs

| Input (form) | Unit | Output (results table) | Unit |
|---|---|---|---|
| VCC | V | VTH, VB, VE, VC, VCE | V |
| R1, R2, RC, RE | kΩ | RTH | kΩ |
| β (current gain) | — | IB | µA |
| VBE | V | IC, IE | mA |

Invalid input (non-numeric, VCC ≤ 0, any R ≤ 0, β ≤ 0) shows a red
error box; the page never crashes.

## Verification dataset

Reference case used by the tests (see `docs/validation.md` for the
full hand calculation): VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ,
RE=1 kΩ, β=100, VBE=0.70 V → **IC = 1.230 mA, VCE = 8.052 V,
Forward-Active**.

## Limitations

- Fixed β and VBE (no Ebers-Moll, no temperature effects)
- DC bias only — no AC small-signal, transient, or Bode analysis
  (later labs extend this app)
- Results in cutoff or saturation are flagged as unreliable rather
  than solved with a saturation model

## Project layout

```
app.py                  Flask routes (HTTP only)
dc_bias.py              engineering calculations (SI units, no HTTP)
templates/index.html    form + results page (Jinja)
static/style.css        presentation
tests/                  unittest suite (math + HTTP)
docs/                   design note, validation, reflection
```

## Reflection — คำตอบรายบุคคล (Lab 02)

คำตอบความเข้าใจหลังลงมือทำ Lab จริง (ฉบับเต็มอยู่ที่ `docs/reflection.md`)

### 1. เหตุใดการเปิด `templates/index.html` ตรง ๆ จึงไม่เท่ากับการรัน Flask?

ไฟล์ `index.html` เป็น Jinja template ที่มี `{{ ... }}` อยู่ข้างใน ถ้าเปิดตรง ๆ
ใน browser จะไม่มีใครประมวลผลส่วนเหล่านี้ — ค่าในช่องกรอกและผลลัพธ์จะว่างเปล่า
และฟอร์มมี `action` ชี้ไปที่ route `/calculate` ของ Flask ด้วย `method="post"`
เมื่อไม่มี server รันอยู่ การกดปุ่ม Calculate จึงไม่มีการคำนวณเกิดขึ้น ต้องรัน
Flask เพื่อให้ `render_template` แปลง template เป็น HTML จริง และเป็นผู้รับ–ส่ง
ข้อมูลระหว่าง browser กับโค้ด Python

### 2. ฟอร์มส่งข้อมูลไป Python อย่างไร?

เมื่อกดปุ่ม Calculate browser จะส่ง HTTP POST พร้อมค่าทุกช่อง
(`vcc, r1, r2, rc, re, beta, vbe`) ไปยัง route `/calculate` ตามที่ฟอร์มระบุ
ไว้ใน `method` และ `action` ฝั่ง Flask รับค่าด้วย `request.form.get(...)`
แปลงหน่วยตัวต้านทานจาก kΩ เป็น Ω (×1000) แล้วส่งต่อให้ฟังก์ชัน
`analyze_dc_bias()` ใน `dc_bias.py` ซึ่งเป็นคนคำนวณจริงทั้งหมด จากนั้น Flask
นำผลลัพธ์กลับมาเติมใส่ template แล้วส่งหน้าเว็บกลับมาให้ browser

### 3. แก้สมการใน `dc_bias.py` แล้วต้องแก้ HTML หรือไม่?

โดยหลักไม่ต้องแก้ HTML เพราะ template มีหน้าที่แสดงผลเท่านั้น ไม่มีสมการ
ฟิสิกส์อยู่ข้างใน ค่า VB, VE, VC, VCE, IC ทั้งในตารางผลลัพธ์และบนแผนผังวงจร
จะเปลี่ยนตามผลการคำนวณใหม่ของ module โดยอัตโนมัติ สิ่งที่ต้องแก้ตามคือ
expected values ในไฟล์ test และเอกสารอ้างอิง (เช่น IC=1.230 mA,
VCE=8.052 V) ส่วน template จะต้องแก้เฉพาะกรณีที่ชื่อหรือหน่วยของ output
เปลี่ยนไปจากเดิม

### 4. ทำไมผลใน Region ที่แบบจำลองใช้ไม่ได้จึงต้องมี Warning?

แบบจำลอง forward-active สมมติว่า VBE คงที่และ IC = β·IB ซึ่งเป็นจริง
เฉพาะเมื่อทรานซิสเตอร์ทำงานใน active region เท่านั้น ถ้า VTH ≤ VBE ฐาน
จะไม่ถูก bias จนนำกระแส (cutoff) และถ้า VCE < 0.2 V ทรานซิสเตอร์จะเข้าสู่
saturation ในสองกรณีนี้ตัวเลขที่สมการคำนวณออกมาไม่สะท้อนพฤติกรรมจริงของ
วงจร (เช่น ได้ VCE ติดลบซึ่งเป็นไปไม่ได้) วิศวกรที่อ่านผลจึงต้องถูกแจ้งให้รู้ว่า
ค่าเหล่านี้ใช้ออกแบบต่อไม่ได้ แอปจึงแสดง warning แทนการแสดงตัวเลขเฉย ๆ
จนผู้ใช้เข้าใจผิดว่าค่านั้นเชื่อถือได้

### สิ่งที่ได้เรียนรู้เพิ่มเติม

ได้ฝึกทำงานแบบ TDD — เขียน test ก่อนโค้ด และยืนยันว่า test ล้มเหลวจริง
ก่อนเขียน implementation (RED → GREEN) รวมถึงเคยพิสูจน์ว่า test เฝ้าโค้ด
จริงโดยลบ `try/except` ชั่วคราวแล้วดู test ล้มทันที ทำให้มั่นใจว่า suite ไม่
ได้ "ผ่านเฉย ๆ" นอกจากนี้ยังเห็นประโยชน์ของการแบ่งโปรเจกต์เป็นหลายไฟล์ —
engineering module (`dc_bias.py`) แยกจาก web layer (`app.py`) และ
presentation (template/CSS) ทำให้แก้สมการโดยไม่กระทบหน้าเว็บ และการ
commit ทีละขั้นตอนผ่าน GitHub Desktop ทำให้ประวัติงานสะอาด ตรวจสอบ
ย้อนหลังได้ทุกขั้น
