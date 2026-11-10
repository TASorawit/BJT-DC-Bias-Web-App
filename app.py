"""Flask web application for the BJT DC Bias Calculator (Lab 02).

Routes:
- GET  /          : render the input form with default values
- POST /calculate : read form values, convert kOhm to Ohm, call the
                    engineering module and render the DC operating point

Unit policy: the form collects resistances in kOhm and voltages in volts;
everything is converted to SI (ohm) BEFORE calling dc_bias.analyze_dc_bias.
This file contains HTTP handling only; no circuit equations live here.
"""

from flask import Flask, render_template, request

from dc_bias import analyze_dc_bias, BiasError

app = Flask(__name__)

# Field order drives the form layout; values are the lab reference set.
DEFAULTS = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}

# Form field name -> (display name, is resistance in kOhm)
FIELDS = {
    "vcc": ("VCC", False),
    "r1": ("R1", True),
    "r2": ("R2", True),
    "rc": ("RC", True),
    "re": ("RE", True),
    "beta": ("beta", False),
    "vbe": ("VBE", False),
}


@app.route("/")
def index():
    return render_template("index.html", form=DEFAULTS, results=None, error=None)


@app.route("/calculate", methods=["POST"])
def calculate():
    form = {name: request.form.get(name, "") for name in FIELDS}

    values = {}
    error = None
    for name, (display, is_resistance) in FIELDS.items():
        raw = form[name]
        try:
            value = float(raw)
        except (TypeError, ValueError):
            error = f"{display} must be a number"
            break
        if is_resistance:
            value *= 1000.0  # kOhm -> Ohm
        values[name] = value

    results = None
    if error is None:
        try:
            results = analyze_dc_bias(**values)
        except BiasError as exc:
            error = str(exc)

    return render_template("index.html", form=form, results=results, error=error)


if __name__ == "__main__":
    app.run(debug=True)
