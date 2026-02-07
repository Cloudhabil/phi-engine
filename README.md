# Phi-Engine

Zero-parameter algebraic prediction engine based on the golden ratio (PHI).

Phi-Engine maps any positive value into **D-space** — a logarithmic coordinate system where multiplicative cascades become additive sums, energy is always conserved (E = 2pi), and bottlenecks surface as the largest term in a simple sum.

## Features

- **D-space transforms** — `D(x) = -ln(x)/ln(PHI)` linearises efficiency cascades
- **Sum-rule validation** — verify that correction coefficients close algebraically
- **Fibonacci decomposition** — decompose integers into GUT representations
- **53 physics constants** — predicted from PHI with ppm-level accuracy
- **Pluggable adapters** — calibration, sensor fusion, photosynthesis/carbon capture
- **Zero core dependencies** — stdlib `math` only; optional extras for API, demo, notebooks

## Quick Start

### Install

```bash
# Core only (zero dependencies)
pip install -e .

# With Streamlit demo
pip install -e ".[demo]"

# With FastAPI server
pip install -e ".[api]"

# Everything
pip install -e ".[full]"
```

### Python SDK

```python
from phi_engine import PhiEngine, D, PHI, Energy

engine = PhiEngine()

# Transform values to D-space
engine.transform([0.5, 1.0, 2.0])
# [1.4404, 0.0, -1.4404]

# Energy is always 2*pi
Energy(0.5)   # 6.283185...
Energy(42.0)  # 6.283185...

# Validate a sum rule
engine.validate([-1, 1, 2, 0.5], expected_sum=2.5)
# {"valid": True, "deviation_ppm": 0.0, ...}

# Fibonacci-decompose a dimension
engine.decompose(45)
# {"group": "SO(10) adj", "fibonacci_form": "F(4)^2 * F(5) = 45", ...}
```

### Adapters

Adapters let you apply D-space analysis to domain-specific problems. Register one and call `engine.run()`:

```python
from phi_engine.adapters.calibration import CalibrationAdapter

engine.register_adapter("calibration", CalibrationAdapter())

result = engine.run("calibration", {
    "readings": [0.98, 1.01, 0.995, 1.003, 0.997],
    "reference": 1.0,
    "instrument": "sensor-001",
})
print(result["consistency_score"])   # 0.999...
print(result["recommendations"])     # ["Instrument within calibration tolerance."]
```

### Photosynthesis / Carbon Capture Adapter

Analyse artificial photosynthesis efficiency cascades, score MOF materials for CO2 capture, and model full systems:

```python
from phi_engine.adapters.photosynthesis import PhotosynthesisAdapter
from phi_engine.photosynthesis_constants import NATURAL_STEPS

engine.register_adapter("photosynthesis", PhotosynthesisAdapter())

# Mode 1: Cascade — find the bottleneck in a multi-step process
result = engine.run("photosynthesis", {
    "mode": "cascade",
    "steps": NATURAL_STEPS,         # 7-step plant photosynthesis
    "target_efficiency": 0.20,
})
print(result["bottleneck"])          # carbon_fixation (D=1.66)
print(result["recommendations"])     # Suggests engineering RuBisCO

# Mode 2: MOF Filter — rank CO2 capture materials
result = engine.run("photosynthesis", {
    "mode": "mof_filter",
    "candidates": ["ZIF-8", "MOF-74-Mg", "Fe-BTC", "UiO-66"],
    "constraints": {"abundant_only": True},
})
for m in result["mof_ranking"]:
    print(f'{m["name"]}: score={m["score"]:.1f}')

# Mode 3: Full System — cascade + MOF + quantum coherence
result = engine.run("photosynthesis", {
    "mode": "full_system",
    "steps": NATURAL_STEPS,
    "mof": "Fe-BTC",
    "coherence_coupling": 0.8,
    "temperature_c": 25,
    "co2_ppm": 415,
    "solar_irradiance_w_m2": 1000,
})
print(f'CO2 captured: {result["co2_per_m2_day_kg"]:.4f} kg/m2/day')
```

## Streamlit Demo

A 5-tab interactive application:

1. **D-Space Explorer** — transform values, verify energy conservation
2. **Calibration Tool** — upload instrument readings for drift analysis
3. **Constants Database** — browse 53 PHI-predicted physics constants
4. **API Playground** — test SDK endpoints interactively
5. **Carbon Lab** — photosynthesis cascades, MOF filter design, full system modelling

### Run locally

```bash
pip install -e ".[demo]"
streamlit run phi_engine/demo/app.py
```

Open `http://localhost:8501` in your browser.

### Run with Docker

```bash
cd phi_engine/demo
docker-compose up --build
```

Services:
- Streamlit UI: `http://localhost:8501`
- FastAPI: `http://localhost:8200`
- Stripe webhook: `http://localhost:4242`

## FastAPI Server

```bash
pip install -e ".[api]"
phi-engine
# Runs on http://localhost:8200
```

Endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/transform` | D-space transform |
| POST | `/analyze` | Run adapter analysis |
| GET | `/constants` | Browse constants DB |
| GET | `/ladder` | PHI-power energy ladder |
| POST | `/validate` | Sum-rule validation |
| POST | `/decompose` | Fibonacci decomposition |

## Jupyter Notebooks

```bash
pip install -e ".[notebooks]"
jupyter notebook notebooks/
```

- `01_getting_started.ipynb` — D-space transforms, energy conservation, basics
- `02_calibration_demo.ipynb` — Calibration workflow with real data

## Project Structure

```
phi_engine/
  core.py                   # D(x), Theta(x), Energy(x), constants
  engine.py                 # PhiEngine facade
  analyzer.py               # Sum-rule, decomposition, consistency
  ladder.py                 # PHI-power energy ladder
  constants_db.py           # 53 physics constants
  photosynthesis_constants.py  # Photon yields, MOF materials, helpers
  adapters/
    base.py                 # BaseAdapter ABC
    calibration.py          # Instrument calibration
    sensor_fusion.py        # Multi-sensor fusion
    photosynthesis.py       # Cascade + MOF + coherence
  api/
    server.py               # FastAPI (port 8200)
    schemas.py              # Pydantic models
  demo/
    app.py                  # Streamlit (5 tabs)
    database.py             # SQLite persistence
    payment.py              # Stripe integration
    webhook.py              # Stripe webhooks
  notebooks/
    01_getting_started.ipynb
    02_calibration_demo.ipynb
```

## Core Maths

```
PHI   = (1 + sqrt(5)) / 2 = 1.6180339887498949
D(x)  = -ln(x) / ln(PHI)          Dimension from value
x(D)  = 1 / PHI^D                 Value from dimension
E(x)  = PHI^D(x) * 2*pi*x = 2*pi  Energy conservation (proven)
```

**Key property**: for a cascade of efficiencies `eta_1 * eta_2 * ... * eta_n`:

```
D(eta_total) = D(eta_1) + D(eta_2) + ... + D(eta_n)
```

The step with the largest D-value is the bottleneck.

## License

MIT
