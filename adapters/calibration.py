"""
phi_engine.adapters.calibration — Precision instrument calibration.

Demonstrates full pipeline: ingest -> D-space -> sum-rule -> report.
Zero external dependencies beyond phi_engine.core.
"""
from __future__ import annotations

from statistics import mean, stdev

from ..analyzer import ConsistencyChecker, SumRuleValidator
from ..core import D, x_from_D
from .base import AdapterConfig, AnalysisResult, BaseAdapter


class CalibrationAdapter(BaseAdapter):
    """Precision calibration using D-space linearisation + sum-rule validation.

    Input data format::

        {
            "readings": [float, ...],   # measured values
            "reference": float,          # known reference value
            "instrument": str,           # instrument identifier
        }
    """

    def __init__(self, config: AdapterConfig | None = None) -> None:
        if config is None:
            config = AdapterConfig(
                name="calibration",
                version="0.1.0",
                description="Precision calibration via D-space linearisation",
            )
        super().__init__(config)
        self._validator = SumRuleValidator()
        self._checker = ConsistencyChecker()

    def ingest(self, raw_data: dict) -> dict:
        """Transform readings to D-space residuals relative to reference."""
        readings: list[float] = raw_data.get("readings", [])
        reference: float = raw_data.get("reference", 1.0)
        instrument: str = raw_data.get("instrument", "unknown")

        if not readings:
            return {"error": "No readings provided", "d_readings": [], "d_ref": 0.0}
        if reference <= 0:
            return {"error": "Reference must be > 0", "d_readings": [], "d_ref": 0.0}

        d_ref = D(reference)
        d_readings = [D(abs(r)) if r > 0 else float("nan") for r in readings]
        d_residuals = [dr - d_ref for dr in d_readings if dr == dr]  # skip NaN

        return {
            "d_readings": d_readings,
            "d_ref": d_ref,
            "d_residuals": d_residuals,
            "reference": reference,
            "instrument": instrument,
            "n_readings": len(readings),
            "raw_readings": readings,
        }

    def analyze(self, d_data: dict) -> AnalysisResult:
        """Analyse D-space residuals for systematic drift and corrections."""
        if "error" in d_data:
            return AnalysisResult(
                success=False,
                data=d_data,
                d_space_values=[],
                consistency_score=0.0,
                hierarchy=[],
                recommendations=[d_data["error"]],
            )

        residuals: list[float] = d_data["d_residuals"]
        raw: list[float] = d_data.get("raw_readings", [])

        if len(residuals) < 2:
            return AnalysisResult(
                success=False,
                data=d_data,
                d_space_values=residuals,
                consistency_score=0.0,
                hierarchy=[],
                recommendations=["Need at least 2 valid readings"],
            )

        # 1. Summary statistics in D-space
        d_mean = mean(residuals)
        d_std = stdev(residuals)

        # 2. Correction coefficients: each reading's deviation normalised
        c_values = [r / d_mean if d_mean != 0 else 0 for r in residuals]

        # 3. Sum-rule: corrections should sum to N (number of readings)
        n = len(residuals)
        sr = self._validator.validate(c_values, float(n), tolerance_ppm=1000)

        # 4. Consistency score: 1.0 = perfect, 0.0 = very bad
        ppm = sr["deviation_ppm"]
        consistency = max(0.0, 1.0 - ppm / 1e6)

        # 5. Corrected values: apply D-space mean shift
        corrected = [x_from_D(D(abs(r)) - d_mean) if r > 0 else r for r in raw]

        # 6. Drift detection
        drift_direction = "positive" if d_mean > 0 else "negative" if d_mean < 0 else "none"
        drift_magnitude = abs(d_mean)

        recommendations: list[str] = []
        if drift_magnitude > 0.1:
            recommendations.append(
                f"Systematic {drift_direction} drift detected "
                f"(D-space magnitude {drift_magnitude:.4f}). "
                "Recalibrate instrument."
            )
        if d_std > 0.05:
            recommendations.append(
                f"High D-space variance ({d_std:.4f}). "
                "Check for environmental interference."
            )
        if not recommendations:
            recommendations.append("Instrument within calibration tolerance.")

        return AnalysisResult(
            success=True,
            data={
                "d_mean": d_mean,
                "d_std": d_std,
                "correction_coefficients": c_values,
                "sum_rule": sr,
                "corrected_values": corrected,
                "drift": {
                    "direction": drift_direction,
                    "magnitude": drift_magnitude,
                },
            },
            d_space_values=residuals,
            consistency_score=consistency,
            hierarchy=[],
            recommendations=recommendations,
        )

    def report(self, result: AnalysisResult) -> dict:
        """Generate a calibration report."""
        data = result.data
        return {
            "adapter": self.config.name,
            "success": result.success,
            "consistency_score": round(result.consistency_score, 6),
            "drift": data.get("drift", {}),
            "d_space_summary": {
                "mean": data.get("d_mean", 0),
                "std": data.get("d_std", 0),
                "n_readings": len(result.d_space_values),
            },
            "sum_rule": data.get("sum_rule", {}),
            "corrected_values": data.get("corrected_values", []),
            "recommendations": result.recommendations,
        }
