"""
phi_engine.api.schemas — Pydantic request / response models.

Requires: pydantic>=2.0  (optional dependency [api])
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------
class TransformRequest(BaseModel):
    values: list[float] = Field(..., min_length=1)
    mode: str = Field("d_space", pattern="^(d_space|phi_power|inverse)$")


class TransformResponse(BaseModel):
    original: list[float]
    transformed: list[float]
    mode: str
    consistency_score: float


# ---------------------------------------------------------------------------
# Analyze
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    adapter: str = Field(..., min_length=1)
    data: dict


class AnalyzeResponse(BaseModel):
    success: bool
    result: dict
    d_space_values: list[float]
    consistency_score: float
    recommendations: list[str]


# ---------------------------------------------------------------------------
# Validate (sum-rule)
# ---------------------------------------------------------------------------
class ValidateRequest(BaseModel):
    coefficients: list[float] = Field(..., min_length=1)
    expected_sum: float
    tolerance_ppm: float = 100


class ValidateResponse(BaseModel):
    valid: bool
    actual_sum: float
    expected_sum: float
    deviation_ppm: float
    residual: float


# ---------------------------------------------------------------------------
# Decompose
# ---------------------------------------------------------------------------
class DecomposeRequest(BaseModel):
    dimension: int = Field(..., gt=0)


class DecomposeResponse(BaseModel):
    dimension: int
    group: str
    fibonacci_form: str | None
    fibonacci_factors: dict


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class ConstantEntry(BaseModel):
    name: str
    value: float
    experimental: float
    unit: str
    sector: str
    formula: str
    deviation_ppm: float


class ConstantsResponse(BaseModel):
    constants: list[ConstantEntry]
    total: int


# ---------------------------------------------------------------------------
# Ladder
# ---------------------------------------------------------------------------
class LadderEntry(BaseModel):
    n: int
    phi_power: float
    energy_GeV: float
    x_from_D: float
    label: str | None = None
    description: str | None = None


class LadderResponse(BaseModel):
    ladder: list[LadderEntry]
    total: int


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = "ok"
    engine: str = "phi-engine"
    version: str = "1.618.0"
