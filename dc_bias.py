"""BJT Common-Emitter DC bias analysis (Voltage-Divider Bias).

Model assumptions (forward-active approximation):
- NPN transistor with constant beta and constant VBE
- R1 from VCC to base, R2 from base to ground (Thevenin: VTH, RTH)
- RC from VCC to collector, RE from emitter to ground

All inputs and outputs use SI units (volts, ohms, amperes).
This module contains engineering calculations only: no HTML, no HTTP.
"""


class BiasError(ValueError):
    """Raised when circuit inputs are missing, non-numeric, or non-positive."""


CUTOFF_WARNING = (
    "Cutoff: VTH <= VBE — the base-emitter junction is not forward-biased; "
    "the transistor is OFF and the forward-active model does not apply."
)
SATURATION_WARNING = (
    "Saturation warning: VCE < 0.2 V — the forward-active approximation "
    "is not valid; results are not reliable."
)
SATURATION_THRESHOLD_V = 0.2


def _validate(vcc, r1, r2, rc, re, beta, vbe):
    """Raise BiasError with a readable message for invalid inputs."""
    checks = [
        ("VCC", vcc, True),
        ("R1", r1, True),
        ("R2", r2, True),
        ("RC", rc, True),
        ("RE", re, True),
        ("beta", beta, True),
        ("VBE", vbe, False),
    ]
    for name, value, must_be_positive in checks:
        if not isinstance(value, (int, float)):
            raise BiasError(f"{name} must be a number")
        if must_be_positive and value <= 0:
            raise BiasError(f"{name} must be greater than 0")


def analyze_dc_bias(vcc, r1, r2, rc, re, beta, vbe):
    """Compute the DC operating point of a voltage-divider-biased NPN
    common-emitter stage.

    Parameters are SI: vcc [V], r1/r2/rc/re [ohm], beta [-], vbe [V].
    Returns a dict with keys vth, rth, ib, ic, ie, vb, ve, vc, vce (SI
    units: V, ohm, A), region ("forward-active" | "cutoff" |
    "saturation") and warnings (list of strings).

    Raises BiasError for non-numeric inputs, or VCC/R/beta <= 0.
    """
    _validate(vcc, r1, r2, rc, re, beta, vbe)

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    if vth <= vbe:
        return {
            "vth": vth,
            "rth": rth,
            "ib": 0.0,
            "ic": 0.0,
            "ie": 0.0,
            "vb": vth,
            "ve": 0.0,
            "vc": vcc,
            "vce": vcc,
            "region": "cutoff",
            "warnings": [CUTOFF_WARNING],
        }

    ib = (vth - vbe) / (rth + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    warnings = []
    region = "forward-active"
    if vce < SATURATION_THRESHOLD_V:
        region = "saturation"
        warnings.append(SATURATION_WARNING)

    return {
        "vth": vth,
        "rth": rth,
        "ib": ib,
        "ic": ic,
        "ie": ie,
        "vb": vb,
        "ve": ve,
        "vc": vc,
        "vce": vce,
        "region": region,
        "warnings": warnings,
    }
