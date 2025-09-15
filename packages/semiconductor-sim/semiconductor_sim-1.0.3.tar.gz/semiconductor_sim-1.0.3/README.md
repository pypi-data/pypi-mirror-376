# SemiconductorSim

SemiconductorSim is an open-source Python library designed to simulate
fundamental semiconductor devices, making complex semiconductor physics
accessible to undergraduate students. Accompanied by interactive tutorials
and comprehensive examples, this library serves as a valuable educational tool
for students, educators, and enthusiasts in the fields of electronics and
semiconductor engineering.

[![CI](https://github.com/kennedym-ds/semiconductor_sim/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/kennedym-ds/semiconductor_sim/actions/workflows/ci.yml?query=branch%3Amain)
[![CodeQL](https://github.com/kennedym-ds/semiconductor_sim/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/kennedym-ds/semiconductor_sim/actions/workflows/codeql.yml?query=branch%3Amain)
<!-- PyPI badge hidden until first release
[![PyPI](https://img.shields.io/pypi/v/semiconductor-sim.svg)](https://pypi.org/project/semiconductor-sim/)
-->
![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue)
[![License](https://img.shields.io/github/license/kennedym-ds/semiconductor_sim.svg)](LICENSE)
[![Coverage](https://img.shields.io/codecov/c/github/kennedym-ds/semiconductor_sim?branch=main)](https://app.codecov.io/gh/kennedym-ds/semiconductor_sim)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-blue.svg)](https://kennedym-ds.github.io/semiconductor_sim/)

## 🧭 Table of Contents

- Installation
- Features
- Supported Devices
- Quickstart
- Examples & Docs
- Units & Conventions
- Interactive Notebooks
- Development
- Troubleshooting
- Contributing
- License
- Releases

## 📚 Features

- PN Junction Diode Simulation: IV, SRH recombination, temperature dependence
- LED Simulation: IV with emission, efficiency model, temperature effects
- Solar Cell Simulation: IV under illumination, short/open-circuit conditions
- Tunnel, Varactor, Zener, MOS Capacitor: teaching-focused models and plots
- Interactive Visualizations: Jupyter widgets and Plotly/Matplotlib support
- Documentation: API references, tutorials, and example scripts

## 🧪 Supported Devices

- PN Junction Diode: Ideal diode with SRH recombination and temperature effects.
- LED: Diode IV with emission intensity; simple efficiency model.
- Solar Cell: IV under illumination; short/open-circuit conditions.
- Tunnel Diode: Simplified IV with correct reverse-bias behavior for teaching.
- Varactor Diode: Junction capacitance vs. reverse bias; IV characteristic.
- Zener Diode: Breakdown behavior with optional ML-predicted Zener voltage.
- MOS Capacitor: C–V and I–V characteristics with depletion width model.

## 🔧 Installation

Install from PyPI (recommended):

```bash
pip install semiconductor-sim
```

From source (editable):

```bash
git clone https://github.com/kennedym-ds/semiconductor_sim.git
cd semiconductor_sim
python -m venv .venv
. .venv/Scripts/activate
pip install -U pip
pip install -r requirements.txt
pip install -e .
```

## 🚀 Quickstart

Minimal PN junction example (no plotting required):

```python
import numpy as np
from semiconductor_sim.devices import PNJunctionDiode

diode = PNJunctionDiode(doping_p=1e17, doping_n=1e17, temperature=300)
V = np.array([0.0, 0.2, 0.4])
I, R = diode.iv_characteristic(V, n_conc=1e16, p_conc=1e16)
print("Current:", I)
print("Recombination (SRH):", R)
```

LED quick preview (two-value return when concentrations omitted):

```python
import numpy as np
from semiconductor_sim.devices import LED

led = LED(doping_p=1e17, doping_n=1e17, temperature=300)
V = np.linspace(0, 2, 5)
current, emission = led.iv_characteristic(V)
```

## 📓 Examples & Docs

- Examples: see the `examples/` folder for scripts and Jupyter notebooks
  (interactive versions use ipywidgets/plotly).
- API docs: browse module docstrings and examples until hosted docs are added.

## 📐 Units & Conventions

- Length: cm; Area: cm²; Volume: cm³; Charge: C; Capacitance: F.
- Doping and carrier concentrations: cm⁻³.
- Temperature: K (default `DEFAULT_T = 300 K`).
- Constants available via `semiconductor_sim.utils.constants`: `q`, `k_B`,
  `epsilon_0`, `DEFAULT_T`.
- Return shapes: device `iv_characteristic` methods return arrays aligned to
  the input `voltage_array`. Where scalar recombination is computed, it is
  broadcast to match the voltage vector.

## 💡 Interactive Notebooks

- Explore interactive notebooks in `examples/` with Jupyter and ipywidgets.
- Launch Jupyter:

```bash
python -m pip install jupyter ipywidgets
jupyter notebook examples
```

If running on a headless server/CI, plotting uses Matplotlib’s
non-interactive backend automatically inside plotting helpers.

## 🖼️ Plotting Helper (Headless-Safe)

To keep plots consistent and CI-friendly, device plotting functions call
lightweight helpers:

- `semiconductor_sim.utils.plotting.use_headless_backend("Agg")`:
  switch to a non-interactive backend before any figures are created.
- `semiconductor_sim.utils.plotting.apply_basic_style()`:
  apply minimal, consistent rcParams (grid, sizes, legend).

When writing new scripts that use Matplotlib directly, you can opt-in to the
same behavior:

```python
from semiconductor_sim.utils.plotting import (
  use_headless_backend,
  apply_basic_style,
)
use_headless_backend("Agg")
apply_basic_style()

import matplotlib.pyplot as plt
# ... your plotting code ...
```

Notes:

- Prefer relying on device `.plot_*` helpers where available.
- Avoid calling `plt.switch_backend` at runtime; set backend via the helper
  before any figures are created.

## 🧑‍💻 Development

Set up a virtual environment and install dev tools:

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -U pip
pip install -r requirements.txt
pip install -e .
pip install ruff mypy pytest pre-commit
pre-commit install
```

Run checks:

```bash
ruff check .
ruff format --check .
mypy .
pytest -q
```

CI runs Ruff, Mypy, and tests across Python 3.10–3.13 on
Linux/Windows/macOS with coverage thresholds. It includes dependency
review, pip-audit security checks, and CodeQL scanning. Dependabot keeps
GitHub Actions and pip dependencies updated. Publishing to PyPI is
automated on tags `v*.*.*`. See `CHANGELOG.md` for notable changes.

## 🩺 Troubleshooting

- "FigureCanvasAgg is non-interactive" warnings: safe to ignore in headless runs.
- Missing ML model for Zener voltage: library falls back to the configured
  default and prints a notice. You can train your own model and place the
  `zener_voltage_rf_model.pkl` under `semiconductor_sim/models/` if desired.
- On Windows, ensure you activate the venv before running commands:

```powershell
. .\.venv\Scripts\Activate.ps1
```

## 🤝 Contributing

Contributions are welcome! Please see `CONTRIBUTING.md` for guidelines. Typical flow:

```bash
git checkout -b feature/my-improvement
ruff check . && mypy . && pytest -q
```

Open a PR; CI runs lint, types, tests, CodeQL, and dependency review.

## ✅ Quality Checks

Before opening a PR, run the core checks locally:

```powershell
ruff check .
ruff format --check .
mypy .
pytest -q
```

See the detailed checklist in the PR template:

- `.github/pull_request_template.md`

## 📄 License

This project is licensed under the MIT License — see `LICENSE`.

## 🏷️ Releases

- Versioning: semantic (`MAJOR.MINOR.PATCH`).
- Publishing: push a tag like `v0.1.1` to trigger the publish workflow.
