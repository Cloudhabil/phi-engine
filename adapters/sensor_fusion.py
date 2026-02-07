"""
phi_engine.adapters.sensor_fusion — Multi-sensor D-space fusion.

Fuses readings from heterogeneous sensors by mapping each to D-space,
weighting by consistency, and producing a unified estimate.
Zero external dependencies beyond phi_engine.core.
"""
from __future__ import annotations

from statistics import mean, stdev

from ..analyzer import ConsistencyChecker, SumRuleValidator
from ..core import D, x_from_D
from .base import AdapterConfig, AnalysisResult, BaseAdapter


class SensorFusionAdapter(BaseAdapter):
    """Multi-sensor fusion using D-space linearisation.

    Input data format::

        {
            "sensors": [
                {
                    "name": "sensor_A",
                    "readings": [float, ...],
                    "weight": float,       # optional, default 1.0
                    "unit": str,           # optional
                },
                ...
            ],
            "reference": float,   # optional ground truth
        }
    """

    def __init__(self, config: AdapterConfig | None = None) -> None:
        if config is None:
            config = AdapterConfig(
                name="sensor_fusion",
                version="0.1.0",
                description="Multi-sensor D-space fusion",
            )
        super().__init__(config)
        self._validator = SumRuleValidator()
        self._checker = ConsistencyChecker()

    def ingest(self, raw_data: dict) -> dict:
        """Transform each sensor's readings to D-space."""
        sensors: list[dict] = raw_data.get("sensors", [])
        reference: float | None = raw_data.get("reference")

        if not sensors:
            return {"error": "No sensors provided", "sensor_data": []}

        d_ref = D(reference) if reference and reference > 0 else None

        sensor_data: list[dict] = []
        for s in sensors:
            readings = s.get("readings", [])
            weight = s.get("weight", 1.0)
            name = s.get("name", "unnamed")
            valid = [r for r in readings if r > 0]
            d_vals = [D(r) for r in valid]
            d_mean = mean(d_vals) if d_vals else 0.0
            d_std = stdev(d_vals) if len(d_vals) >= 2 else 0.0

            sensor_data.append({
                "name": name,
                "weight": weight,
                "d_values": d_vals,
                "d_mean": d_mean,
                "d_std": d_std,
                "n_valid": len(valid),
                "n_total": len(readings),
            })

        return {
            "sensor_data": sensor_data,
            "d_ref": d_ref,
            "n_sensors": len(sensors),
        }

    def analyze(self, d_data: dict) -> AnalysisResult:
        """Fuse sensor readings in D-space with consistency weighting."""
        if "error" in d_data:
            return AnalysisResult(
                success=False,
                data=d_data,
                d_space_values=[],
                consistency_score=0.0,
                hierarchy=[],
                recommendations=[d_data["error"]],
            )

        sensor_data: list[dict] = d_data["sensor_data"]
        d_ref: float | None = d_data.get("d_ref")

        if not sensor_data:
            return AnalysisResult(
                success=False,
                data=d_data,
                d_space_values=[],
                consistency_score=0.0,
                hierarchy=[],
                recommendations=["No sensor data to fuse"],
            )

        # 1. Weighted D-space fusion
        total_weight = 0.0
        weighted_d_sum = 0.0
        all_d_values: list[float] = []

        for sd in sensor_data:
            w = sd["weight"]
            # Weight inversely with variance (precision weighting)
            if sd["d_std"] > 0:
                precision_w = w / (sd["d_std"] ** 2)
            else:
                precision_w = w * 1000  # near-zero variance → high precision
            weighted_d_sum += sd["d_mean"] * precision_w
            total_weight += precision_w
            all_d_values.extend(sd["d_values"])

        fused_d = weighted_d_sum / total_weight if total_weight > 0 else 0.0
        fused_value = x_from_D(fused_d)

        # 2. Inter-sensor consistency
        d_means = [sd["d_mean"] for sd in sensor_data if sd["n_valid"] > 0]
        if len(d_means) >= 2:
            inter_std = stdev(d_means)
        else:
            inter_std = 0.0

        # 3. Sum-rule check: sensor weights should be self-consistent
        weights = [sd["weight"] for sd in sensor_data]
        sr = self._validator.validate(weights, sum(weights))

        # 4. Consistency score
        consistency = max(0.0, 1.0 - inter_std)

        # 5. Reference comparison
        ref_deviation = None
        if d_ref is not None:
            ref_deviation = fused_d - d_ref

        # 6. Per-sensor quality ranking
        quality: list[dict] = []
        for sd in sensor_data:
            q = 1.0 - min(sd["d_std"], 1.0)
            quality.append({
                "sensor": sd["name"],
                "quality": round(q, 4),
                "d_mean": sd["d_mean"],
                "d_std": sd["d_std"],
                "n_readings": sd["n_valid"],
            })
        quality.sort(key=lambda x: -x["quality"])

        recommendations: list[str] = []
        if inter_std > 0.1:
            recommendations.append(
                f"High inter-sensor disagreement (D-space std={inter_std:.4f}). "
                "Check for systematic bias in individual sensors."
            )
        low_q = [q for q in quality if q["quality"] < 0.5]
        if low_q:
            names = ", ".join(q["sensor"] for q in low_q)
            recommendations.append(f"Low quality sensors: {names}. Consider recalibration.")
        if not recommendations:
            recommendations.append("All sensors consistent. Fusion reliable.")

        return AnalysisResult(
            success=True,
            data={
                "fused_d": fused_d,
                "fused_value": fused_value,
                "inter_sensor_std": inter_std,
                "ref_deviation": ref_deviation,
                "sensor_quality": quality,
                "sum_rule": sr,
            },
            d_space_values=all_d_values,
            consistency_score=consistency,
            hierarchy=quality,
            recommendations=recommendations,
        )

    def report(self, result: AnalysisResult) -> dict:
        """Generate sensor fusion report."""
        data = result.data
        return {
            "adapter": self.config.name,
            "success": result.success,
            "fused_estimate": {
                "d_space": data.get("fused_d", 0),
                "real_value": data.get("fused_value", 0),
            },
            "consistency_score": round(result.consistency_score, 6),
            "inter_sensor_std": data.get("inter_sensor_std", 0),
            "ref_deviation": data.get("ref_deviation"),
            "sensor_quality": data.get("sensor_quality", []),
            "recommendations": result.recommendations,
        }
