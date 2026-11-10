# BJT DC Bias Web App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Flask web app that computes the DC operating point of an NPN Common-Emitter Voltage-Divider Bias circuit from form input, with validation, region warnings, and tests.

**Architecture:** Pure engineering module (`dc_bias.py`, SI units, no HTTP/HTML) consumed by Flask routes (`app.py`) that parse the kΩ form, convert units, and render a single Jinja template showing form + results + errors + warnings on one page. unittest suite covers both the math and the HTTP layer.

**Tech Stack:** Python 3.14 (this machine: launch with `py`), Flask 3.x, stdlib `unittest`. No other dependencies.

**Spec:** `docs/design-note.md` (approved) — the plan argues from it; executors read both.

## Global Constraints

- `dc_bias.py` must not import flask or reference HTML/HTTP; `templates/index.html` must not contain physics equations (unit display scaling like ×1000 for mA is allowed).
- Internal SI units everywhere in the module: volts, ohms, **amperes**. The kΩ→Ω conversion (×1000) happens only in `app.py`; A→mA display conversion happens only in the template.
- Default form values = spec reference set: VCC=12, R1=100, R2=22, RC=2.2, RE=1 (kΩ), β=100, VBE=0.70.
- Error/warning copy (exact strings the tests pin):
  - Cutoff: `"Cutoff: VTH <= VBE — the base-emitter junction is not forward-biased; the transistor is OFF and the forward-active model does not apply."`
  - Saturation: `"Saturation warning: VCE < 0.2 V — the forward-active approximation is not valid; results are not reliable."`
  - Non-numeric: `"<NAME> must be a number"` · Non-positive: `"<NAME> must be greater than 0"` (NAME ∈ VCC, R1, R2, RC, RE, beta, VBE).
- Commit steps are executed **by the student in GitHub Desktop** (stated preference): the executor pauses at each checkpoint, hands over the suggested message, and waits.
- Never commit `.venv/`, `__pycache__/`, `*.pyc`, `.env` (Task 3 adds `.gitignore`; until then, keep venv out of `git add`).
- Tests run with `py -m unittest discover -s tests -v` (README also documents `python`/`python3` for other machines).

## Review Focus

1. **Blank form field** (`vcc=""`): expect a clear `VCC must be a number` error, HTTP 200, page renders — pinned in Task 2.
2. **Omitted form field** (POST body missing `rc` entirely): expect the same per-field error, not a 500 — pinned in Task 2 (use `request.form.get(name, "")`).
3. **VTH exactly == VBE boundary** (VCC=7, R1=90k, R2=10k, VBE=0.7 → VTH=0.7): spec says VTH ≤ VBE is cutoff — pinned in Task 1.
4. **Whitespace-only input** (`r1=" "`): treated as non-numeric (float(" ") raises), not a crash — same test class as (1), pinned in Task 2.
5. **Very large β** (β=10000): must compute without error and report a region (VCE ≈ 7.3 V → forward-active) — pinned in Task 1.

---

### Task 1: Engineering module `dc_bias.py`

**Files:**
- Create: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: nothing (stdlib only).
- Produces (used by Task 2):
  - `class BiasError(ValueError)` — raised with one of the error strings above.
  - `def analyze_dc_bias(vcc, r1, r2, rc, re, beta, vbe) -> dict` — all params floats in SI units (V, Ω, dimensionless). Returns dict with keys: `"vth", "rth", "ib", "ic", "ie", "vb", "ve", "vc", "vce"` (SI: V, Ω, A), `"region"` (`"forward-active"` | `"cutoff"` | `"saturation"`), `"warnings"` (list[str], possibly empty).
  - Behavior: raises `BiasError` on non-numeric (not int/float) or VCC/R/β ≤ 0; if `vth <= vbe` → cutoff solution (ib=ic=ie=0, ve=0, vb=vth, vc=vcc, vce=vcc, region="cutoff", cutoff warning); else forward-active equations, and if `vce < 0.2` → region="saturation" + saturation warning (computed values still returned, flagged unreliable).

- [ ] **Step 1: Write the failing tests** — `tests/test_dc_bias.py`

```python
import unittest
from dc_bias import analyze_dc_bias, BiasError

REF = dict(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)


class TestReferenceValues(unittest.TestCase):
    def test_reference_operating_point(self):
        r = analyze_dc_bias(**REF)
        self.assertAlmostEqual(r["vth"], 2.1639, places=3)
        self.assertAlmostEqual(r["rth"], 18032.79, places=1)
        self.assertAlmostEqual(r["ib"] * 1e6, 12.2986, places=2)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.2299, places=3)
        self.assertAlmostEqual(r["ie"] * 1e3, 1.2422, places=3)
        self.assertAlmostEqual(r["vb"], 1.9422, places=3)
        self.assertAlmostEqual(r["ve"], 1.2422, places=3)
        self.assertAlmostEqual(r["vc"], 9.2943, places=3)
        self.assertAlmostEqual(r["vce"], 8.0522, places=3)
        self.assertEqual(r["region"], "forward-active")
        self.assertEqual(r["warnings"], [])

    def test_cutoff_region(self):
        r = analyze_dc_bias(**{**REF, "r2": 1_000.0})   # VTH = 0.1188 V <= VBE
        self.assertEqual(r["region"], "cutoff")
        self.assertEqual((r["ib"], r["ic"], r["ie"]), (0.0, 0.0, 0.0))
        self.assertAlmostEqual(r["vc"], 12.0, places=6)
        self.assertTrue(any("Cutoff" in w for w in r["warnings"]))

    def test_saturation_region(self):
        r = analyze_dc_bias(**{**REF, "rc": 47_000.0})   # VCE goes very negative
        self.assertEqual(r["region"], "saturation")
        self.assertTrue(any("Saturation" in w for w in r["warnings"]))

    def test_vth_equals_vbe_boundary_is_cutoff(self):
        r = analyze_dc_bias(vcc=7.0, r1=90_000.0, r2=10_000.0, rc=2_200.0,
                            re=1_000.0, beta=100.0, vbe=0.70)  # VTH = 0.7 exactly
        self.assertEqual(r["region"], "cutoff")

    def test_large_beta_computes(self):
        r = analyze_dc_bias(**{**REF, "beta": 10_000.0})
        self.assertEqual(r["region"], "forward-active")
        self.assertGreater(r["vce"], 0.2)


class TestValidation(unittest.TestCase):
    def test_non_positive_inputs_raise(self):
        for field, value in [("vcc", 0.0), ("vcc", -5.0), ("r1", 0.0), ("r2", -1.0),
                             ("rc", 0.0), ("re", -2.0), ("beta", 0.0), ("beta", -3.0)]:
            with self.assertRaises(BiasError, msg=field):
                analyze_dc_bias(**{**REF, field: value})

    def test_non_numeric_raises(self):
        with self.assertRaises(BiasError):
            analyze_dc_bias(**{**REF, "vcc": "twelve"})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -m unittest discover -s tests -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 3: Implement `dc_bias.py`**

Layout: module docstring (model assumptions), `BiasError`, a `_validate(...)` helper raising `BiasError` per the error strings, then `analyze_dc_bias` implementing the spec equations in this order: validate → VTH/RTH → cutoff check (`vth <= vbe`) → forward-active equations (IB→IC→IE→VE→VB→VC→VCE) → saturation check (`vce < 0.2`). No algorithm is left open beyond the spec.

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -m unittest discover -s tests -v`
Expected: PASS (7 tests, 0 failures)

- [ ] **Step 5: Commit (student, GitHub Desktop)**

Message: `Add BJT DC bias engineering module with tests`
Files to stage: `dc_bias.py`, `tests/test_dc_bias.py`

---

### Task 2: Flask app, template, CSS, HTTP tests

**Files:**
- Create: `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py`

**Interfaces:**
- Consumes: `analyze_dc_bias(...)`, `BiasError` from `dc_bias` (Task 1 signatures).
- Produces: `app` (Flask object, importable by tests) with routes:
  - `GET /` → renders `index.html` with defaults, no results
  - `POST /calculate` → reads form fields `vcc, r1, r2, rc, re, beta, vbe` (R fields **kΩ**), converts R×1000 to Ω, calls the module, renders `index.html` with `results`, `error`, and sticky form values; `BiasError` → HTTP 200 with error shown
- Form field names (exact): `vcc, r1, r2, rc, re, beta, vbe`

- [ ] **Step 1: Create venv and install Flask (one-time scaffolding)**

Run: `py -m venv .venv` then `.venv\Scripts\python.exe -m pip install flask`
Expected: `Successfully installed flask...` (plus jinja2/werkzeug/etc.)

- [ ] **Step 2: Write the failing tests** — `tests/test_web.py`

```python
import unittest
from app import app

VALID = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.70"}


class TestWeb(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_shows_form(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"VCC", r.data)
        self.assertIn(b'name="r1"', r.data)

    def test_post_valid_returns_reference_results(self):
        r = self.client.post("/calculate", data=VALID)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"8.052", r.data)          # VCE
        self.assertIn(b"1.230", r.data)          # IC in mA
        self.assertIn(b"Forward-Active", r.data)

    def test_post_non_numeric_shows_error(self):
        r = self.client.post("/calculate", data={**VALID, "r1": "abc"})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"must be a number", r.data)

    def test_post_blank_field_shows_error(self):
        r = self.client.post("/calculate", data={**VALID, "vcc": ""})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"must be a number", r.data)

    def test_post_omitted_field_shows_error(self):
        partial = dict(VALID); del partial["rc"]
        r = self.client.post("/calculate", data=partial)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"must be a number", r.data)

    def test_post_cutoff_shows_warning(self):
        r = self.client.post("/calculate", data={**VALID, "r2": "1"})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Cutoff", r.data)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 4: Implement `app.py`**

Structure: create `app = Flask(__name__)`; `GET /` renders template with `DEFAULTS = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.70"}`; `POST /calculate` reads each field with `request.form.get(name, "")`, tries `float(value)` (R fields ×1000), maps failures to the `"<NAME> must be a number"` error, calls `analyze_dc_bias` inside `try/except BiasError`, always renders `index.html` with `status 200` passing `form` (sticky), `results` (dict or None), `error` (str or None). Non-numeric detection and the module's `BiasError` both land in the same `error` string; never let an exception escape the route.

- [ ] **Step 5: Implement `templates/index.html` + `static/style.css`**

One page: form (labels `VCC [V]`, `R1 [kΩ]`, …, defaults/sticky values from `form` dict), submit button `Calculate DC Bias`; results table (VB/VE/VC/VCE in V `%.3f`, IC/IB/IE in mA/µA via `* 1000` / `* 1e6`, RTH in kΩ, VTH in V) with unit column; red error box when `error`; orange warning box listing `results.warnings`; green region badge `Forward-Active` / gray `Cutoff` / orange `Saturation`. CSS: two-column responsive layout, minimal styling, linked via `url_for('static', ...)`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS (13 tests, 0 failures)

- [ ] **Step 7: Manual smoke check in browser**

Run (background): `.venv\Scripts\python.exe -m flask --app app run --debug`
Open `http://127.0.0.1:5000/` → form shows defaults → Calculate → VCE ≈ 8.052 V, region Forward-Active → set R2=1 → Cutoff warning → set R1=abc → error box, page intact. Stop server.

- [ ] **Step 8: Commit (student, GitHub Desktop)**

Message: `Add Flask web app with form, results, warnings and HTTP tests`
Files: `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py` (NOT `.venv/`)

---

### Task 3: Reproducibility — README, docs, project files

**Files:**
- Create: `requirements.txt`, `README.md`, `AGENTS.md`, `.gitignore`, `docs/validation.md`, `docs/reflection.md`

**Interfaces:**
- Consumes: the finished app from Tasks 1–2.
- Produces: nothing code-wise; a repo that satisfies acceptance A7 (clone → install → run → test).

- [ ] **Step 1: Write `.gitignore`, `requirements.txt`, `AGENTS.md`**

`.gitignore`: `.venv/`, `__pycache__/`, `*.pyc`, `.env`. `requirements.txt`: `flask>=3.0`. `AGENTS.md`: short conventions (module purity rule, SI units, tests before code, commit style).

- [ ] **Step 2: Write `README.md`**

Sections: what it is; circuit diagram (ASCII) + model assumptions; install (`py -m venv .venv` or `python -m venv .venv`, pip install -r requirements.txt); run (`flask --app app run --debug`, open `http://127.0.0.1:5000/`); test (`python -m unittest discover -s tests -v`); input/output table with units; limitations (fixed β/VBE, no AC).

- [ ] **Step 3: Write `docs/validation.md` and `docs/reflection.md`**

`validation.md`: the independent hand calculation table (VTH→VCE with worked numbers from the spec set) vs web output, plus invalid-input and region-warning checks — the evidence for A3–A5. `reflection.md`: scaffold the four individual questions from the lab handout with empty answer sections for the student to fill in.

- [ ] **Step 4: Verify reproducibility end-to-end (A7)**

Run: `py -m venv .venv-verify` → `.venv-verify\Scripts\python.exe -m pip install -r requirements.txt` → `.venv-verify\Scripts\python.exe -m unittest discover -s tests -v` → start server from that venv in background → `Invoke-WebRequest http://127.0.0.1:5000/` returns 200 → stop server → delete `.venv-verify`.
Expected: all tests pass; GET / returns 200.

- [ ] **Step 5: Commit (student, GitHub Desktop), then Publish repository**

Message: `Add README, docs and project files for reproducibility`
Files: everything from this task. Then in GitHub Desktop: **Publish repository** (public) → copy URL + latest commit SHA for Moodle.

---

## Self-Review Notes

- Spec coverage: inputs/outputs/units (T1, T2), validation (T1, T2), region warnings (T1, T2), file structure & README/docs (T3), A1–A7 all mapped. Gap check: sticky-form behavior only smoke-tested manually — acceptable (presentation, not acceptance criterion).
- Type consistency: `analyze_dc_bias` keys and `BiasError` strings identical across T1/T2; form field names identical in T2 tests and template.
- Proportion: 3 tasks, each independently testable; no code bodies beyond pinned tests and error strings.
