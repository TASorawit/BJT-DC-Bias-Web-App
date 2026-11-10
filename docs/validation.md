# Validation — BJT DC Bias Web App (Lab 02)

Evidence for acceptance tests A3–A5. All values recomputed by hand from
the forward-active model, then compared against the web app's output.

## Reference case (A3)

Inputs: VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1 kΩ,
β = 100, VBE = 0.70 V

### Independent hand calculation

| Step | Equation | Value |
|---|---|---|
| VTH | 12 × 22k / (100k + 22k) = 264/122 | **2.1639 V** |
| RTH | 100k·22k / 122k | **18.033 kΩ** |
| IB | (2.1639 − 0.70) / (18,033 + 101×1,000) = 1.4639 / 119,033 | **12.30 µA** |
| IC | 100 × 12.30 µA | **1.230 mA** |
| IE | 101 × 12.30 µA | **1.242 mA** |
| VE | 1.242 m × 1k | **1.242 V** |
| VB | 1.242 + 0.70 | **1.942 V** |
| VC | 12 − 1.230 m × 2.2k = 12 − 2.706 | **9.294 V** |
| VCE | 9.294 − 1.242 | **8.052 V** |

Region check: VTH (2.164 V) > VBE (0.70 V) and VCE (8.052 V) > 0.2 V
→ **Forward-Active** ✓

### Web app output (screenshot / browser session)

| Quantity | Hand calc | Web app | Match |
|---|---|---|---|
| VTH | 2.164 V | 2.164 V | ✓ |
| RTH | 18.033 kΩ | 18.033 kΩ | ✓ |
| IB | 12.30 µA | 12.299 µA | ✓ |
| IC | 1.230 mA | 1.230 mA | ✓ |
| IE | 1.242 mA | 1.242 mA | ✓ |
| VE | 1.242 V | 1.242 V | ✓ |
| VB | 1.942 V | 1.942 V | ✓ |
| VC | 9.294 V | 9.294 V | ✓ |
| VCE | 8.052 V | 8.052 V | ✓ |
| Region | Forward-Active | Forward-Active | ✓ |

(Values agree to displayed precision; exact match asserted in
`tests/test_dc_bias.py::test_reference_operating_point`.)

## Invalid input handling (A4)

| Input tried | Expected | Observed |
|---|---|---|
| R1 = `abc` | red error box, page intact, HTTP 200 | ✓ error shown: "R1 must be a number" |
| VCC = blank | error box, HTTP 200 | ✓ "VCC must be a number" |
| RC omitted from POST | error box, HTTP 200 (no crash) | ✓ "RC must be a number" |
| β = 0 / negative R | module raises BiasError → error box | ✓ (unit tests, 8 cases) |

## Region warnings (A5)

| Case | Expected | Observed |
|---|---|---|
| R2 = 1 kΩ (VTH = 0.119 V ≤ VBE) | Cutoff warning, transistor OFF | ✓ warning shown, IB=IC=IE=0, VC=VCC |
| VTH exactly = VBE (7 V, 90k/10k) | Cutoff (boundary is cutoff) | ✓ (unit test) |
| RC = 47 kΩ (VCE far below 0.2 V) | Saturation warning, results flagged unreliable | ✓ warning shown |

## Automated tests

`py -m unittest discover -s tests -v` → **17 tests, all OK**

- 7 engineering tests (`tests/test_dc_bias.py`): reference point,
  cutoff, saturation, VTH=VBE boundary, large β, non-positive inputs
  (8 sub-cases), non-numeric input
- 10 HTTP tests (`tests/test_web.py`): GET form, POST reference results,
  POST non-numeric, POST blank field, POST omitted field, POST cutoff
  warning, POST non-positive input, GET circuit schematic, schematic
  node values after POST, schematic values change with input — all via
  the Flask test client

## Reproducibility (A7)

Verified in a fresh virtual environment (`.venv-verify`, deleted
afterwards): `pip install -r requirements.txt` → suite green →
`GET /` returns HTTP 200. A clone of this repository reproduces the
same behavior following this README.
