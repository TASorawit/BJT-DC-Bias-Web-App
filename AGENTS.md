# AGENTS.md — AI coding conventions for this repo

## Architecture rules

- `dc_bias.py` is a pure engineering module: SI units (V, Ω, A) in and out,
  no Flask imports, no HTML/HTTP knowledge. Circuit equations live ONLY here.
- `app.py` handles HTTP only: form parsing, kΩ→Ω conversion (×1000),
  calling the module, rendering. No physics equations here.
- `templates/index.html` presents results; unit display scaling
  (A→mA/µA, Ω→kΩ) is allowed in the template, physics is not.
- `static/style.css` is presentation only.

## Testing rules

- Test-first: every behavior change gets a failing test before code.
- Engineering math: `tests/test_dc_bias.py`; HTTP routes:
  `tests/test_web.py` via the Flask test client.
- Full suite: `python -m unittest discover -s tests -v` (Windows with
  the `py` launcher: `py -m unittest discover -s tests -v`).
- Reference dataset for verification (VCC=12V, R1=100k, R2=22k,
  RC=2.2k, RE=1k, β=100, VBE=0.7V) → IC=1.230 mA, VCE=8.052 V,
  forward-active. Recompute by hand before changing expected values.

## Commit style

- One logical change per commit, imperative summary line
  (e.g. "Add BJT DC bias engineering module with tests").
- Never commit `.venv/`, `__pycache__/`, `*.pyc`, `.env`.

## Scope discipline (Lab 02)

- DC bias of voltage-divider bias only. No AC, transient, Bode plots,
  extra bias topologies, FET or SPICE in this phase — later labs add
  them on top of this structure.
