# Design Note — BJT DC Bias Web App (Lab 02)

ENG29 2121 · Computer Programming for Electrical Engineers · 2/2569
Status: **Approved** (brainstorming session, 2026-11-10)

## Intent & Why

สร้าง Flask Web Application คำนวณ DC Operating Point ของวงจร NPN Common-Emitter
แบบ Voltage-Divider Bias โดยให้ Python Backend คำนวณจริง (ไม่ใช่ค่า hardcode)
เป็นชิ้นงานแรกของ Virtual Transistor Laboratory ที่จะต่อยอดทุกสัปดาห์
จบ Lab ด้วยเว็บที่เปิดผ่าน `http://127.0.0.1:5000/` ได้ + tests + GitHub commit

## Goals

- ฟอร์มรับ `VCC [V]`, `R1, R2, RC, RE [kΩ]`, `β` (dimensionless), `VBE [V]`
- Backend คำนวณและแสดง: `VTH, RTH, IB, IC, IE, VB, VE, VC, VCE` พร้อมหน่วย
- แจ้ง Operating Region (Forward-Active / Cutoff / Saturation) พร้อม Warning
- Validation ข้อมูลผิด: non-numeric, VCC≤0, R≤0, β≤0 → error ชัดเจน หน้าเว็บไม่ล้ม
- Automated tests: engineering math (unittest) + Flask HTTP (test client)
- ค่า default = ชุดข้อมูลอ้างอิงเอกสาร Lab

## Non-goals (Week 2 ไม่ทำ)

AC / small-signal / transient / Bode plot / signal generator / circuit editor /
bias types อื่น / FET / SPICE solver / overlay animation

## Constraints

- เปิดผ่าน Local Web Server เท่านั้น (ไม่ใช่ `file://`)
- `dc_bias.py` ไม่รู้จัก HTML/HTTP; `templates/index.html` ไม่ฝังสมการฟิสิกส์
- ไม่ commit `.venv/`, `__pycache__/`, `.env`
- Python 3.14 (เครื่องนี้ใช้คำสั่ง `py`), Flask เป็น dependency เดียวที่จำเป็น

## Approaches (พิจารณาแล้วเลือก)

| ทางเลือก | ผลลัพธ์ |
|---|---|
| **Flask multi-file (เลือก)** | ตรงข้อกำหนด Lab: backend คำนวณ, แยกไฟล์ตามความรับผิดชอบ, ทดสอบได้ทั้ง logic และ HTTP |
| HTML ไฟล์เดียว + JS คำนวณ | ตัดทิ้ง — ขัดข้อกำหนด "Python backend คำนวณ + multi-file" |
| Django/FastAPI | ตัดทิ้ง — หนักเกินจำเป็นสำหรับ 3 ชั่วโมง, Lab แนะนำ Flask |

**การตัดสินใจของผู้ใช้:** ช่องกรอกค่า R ใช้หน่วย **kΩ** (พิมพ์ `100` = 100 kΩ)
การแปลง kΩ→Ω เป็นหน้าที่ของ `app.py` — `dc_bias.py` รับ SI ล้วน (Ω, V) เสมอ

## Design

### สมการ (Forward-Active Approximation: β, VBE คงที่)

```
VTH = VCC · R2 / (R1 + R2)          RTH = R1·R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β+1)·RE)
IC  = β·IB                           IE  = (β+1)·IB
VE  = IE·RE                           VB  = VE + VBE
VC  = VCC − IC·RC                     VCE = VC − VE
```

### Validation & Warnings

- Input: ต้องเป็นตัวเลข, VCC > 0, R1,R2,RC,RE > 0, β > 0 → ผิด = `BiasError` (error message อ่านได้)
- `VTH ≤ VBE` → **Cutoff warning** (IB ≤ 0 ไม่มี physical meaning ในแบบจำลองนี้)
- `VCE < 0.2 V` → **Saturation warning** (Forward-Active Approximation ใช้ไม่ได้)
- ทั้งสองกรณีแสดงข้อจำกัด ไม่อ้างว่าเป็นผลจำลองที่แม่นยำ

### File Structure

```
├── app.py                  # Flask routes: GET / (form), POST /calculate
├── dc_bias.py              # pure engineering calculations (SI units)
├── templates/index.html    # form + results table (Jinja)
├── static/style.css        # presentation
├── tests/test_dc_bias.py   # ≥3 engineering math tests
├── tests/test_web.py       # Flask test client tests
├── requirements.txt, README.md, AGENTS.md, .gitignore
└── docs/design-note.md, validation.md, reflection.md
```

### Test Plan (ชุดข้อมูลอ้างอิง)

VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V
→ คำนวณอิสระ (ตรวจสอบซ้ำแล้ว): VTH=2.1639 V, RTH=18.033 kΩ, IB=12.30 µA,
IC=1.230 mA, IE=1.242 mA, VE=1.242 V, VB=1.942 V, VC=9.294 V, VCE=8.052 V
(Forward-Active: VTH>VBE และ VCE>0.2 V)

- `test_dc_bias.py`: ค่าอ้างอิง / invalid inputs (R≤0, β≤0, VCC≤0, non-numeric) / cutoff / saturation
- `test_web.py`: GET 200 มีฟอร์ม / POST ค่าปกติแสดงผล / POST ค่าผิด error ไม่ล้ม / POST cutoff มี warning

## Success Criteria (A1–A7)

เปิด localhost ได้ · POST คำนวณจริง · ผลตรงการคำนวณอิสระ · validation ไม่ล้ม ·
warning region · ≥3+1 tests ผ่าน · clone แล้วรันตาม README ได้
