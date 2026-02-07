"""
phi_engine.api.server — FastAPI REST API on port 8200.

Requires: fastapi, uvicorn, pydantic  (optional dependency [api])

Usage::

    phi-engine          # runs on 0.0.0.0:8200
    uvicorn phi_engine.api.server:app --port 8200
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from ..adapters.calibration import CalibrationAdapter
from ..adapters.photosynthesis import PhotosynthesisAdapter
from ..adapters.sensor_fusion import SensorFusionAdapter
from ..engine import PhiEngine
from .schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ConstantEntry,
    ConstantsResponse,
    DecomposeRequest,
    DecomposeResponse,
    HealthResponse,
    LadderEntry,
    LadderResponse,
    TransformRequest,
    TransformResponse,
    ValidateRequest,
    ValidateResponse,
)

app = FastAPI(
    title="Phi-Engine API",
    description="Zero-parameter algebraic prediction engine based on PHI",
    version="1.618.0",
)

# Singleton engine with built-in adapters
_engine = PhiEngine()
_engine.register_adapter("calibration", CalibrationAdapter())
_engine.register_adapter("sensor_fusion", SensorFusionAdapter())
_engine.register_adapter("photosynthesis", PhotosynthesisAdapter())


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse()


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------
@app.post("/transform", response_model=TransformResponse)
def transform(req: TransformRequest):
    if req.mode == "d_space":
        try:
            transformed = _engine.transform(req.values)
        except ValueError as exc:
            raise HTTPException(400, str(exc))
    elif req.mode == "inverse":
        transformed = _engine.inverse_transform(req.values)
    elif req.mode == "phi_power":
        transformed = [_engine.scale_map(int(v))["phi_power"] for v in req.values]
    else:
        raise HTTPException(400, f"Unknown mode: {req.mode}")

    checks = [_engine.check(v) for v in req.values if v > 0]
    n_valid = sum(
        1 for c in checks
        if c["d_space_closure"]["valid"] and c["energy_conservation"]["valid"]
    )
    score = n_valid / len(checks) if checks else 1.0

    return TransformResponse(
        original=req.values,
        transformed=transformed,
        mode=req.mode,
        consistency_score=round(score, 6),
    )


# ---------------------------------------------------------------------------
# Analyze
# ---------------------------------------------------------------------------
@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if req.adapter not in _engine.list_adapters():
        raise HTTPException(404, f"Adapter '{req.adapter}' not found. "
                            f"Available: {_engine.list_adapters()}")
    result = _engine.run(req.adapter, req.data)
    return AnalyzeResponse(
        success=result.get("success", True),
        result=result,
        d_space_values=result.get("d_space_values", []),
        consistency_score=result.get("consistency_score", 0),
        recommendations=result.get("recommendations", []),
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
@app.get("/constants", response_model=ConstantsResponse)
def list_constants(
    sector: str | None = Query(None),
    query: str | None = Query(None),
):
    entries = _engine.constants.search(sector=sector, query=query)
    return ConstantsResponse(
        constants=[ConstantEntry(**e) for e in entries],
        total=len(entries),
    )


@app.get("/constants/{name}", response_model=ConstantEntry)
def get_constant(name: str):
    entry = _engine.constants.get(name)
    if entry is None:
        raise HTTPException(404, f"Constant '{name}' not found")
    return ConstantEntry(**entry)


# ---------------------------------------------------------------------------
# Ladder
# ---------------------------------------------------------------------------
@app.get("/ladder", response_model=LadderResponse)
def get_ladder(n_max: int = Query(78, ge=1, le=248)):
    entries = _engine.ladder.full_ladder(n_max)
    return LadderResponse(
        ladder=[LadderEntry(**e) for e in entries],
        total=len(entries),
    )


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------
@app.post("/validate", response_model=ValidateResponse)
def validate(req: ValidateRequest):
    result = _engine.validate(req.coefficients, req.expected_sum, req.tolerance_ppm)
    return ValidateResponse(**result)


# ---------------------------------------------------------------------------
# Decompose
# ---------------------------------------------------------------------------
@app.post("/decompose", response_model=DecomposeResponse)
def decompose(req: DecomposeRequest):
    result = _engine.decompose(req.dimension)
    return DecomposeResponse(**result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)


if __name__ == "__main__":
    main()
