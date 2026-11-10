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

13 tests: 7 engineering-math cases in `tests/test_dc_bias.py` and 6
HTTP-route cases in `tests/test_web.py` (Flask test client).

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
