"""
phi_engine.adapters.photosynthesis — Artificial photosynthesis, MOF filter
design, and quantum coherence analysis via D-space.

Three analysis modes:
  1. cascade  — Photosynthesis efficiency cascade (sum-rule validated)
  2. mof_filter — MOF material ranking for CO2 capture
  3. full_system — Combined cascade + MOF + coherence system model

Zero external dependencies beyond phi_engine core.
"""
from __future__ import annotations

from ..analyzer import SumRuleValidator
from ..core import D, x_from_D
from ..photosynthesis_constants import (
    MOF_MATERIALS,
    NATURAL_STEPS,
    PHI_OPTIMAL_PORE_NM,
    co2_factor,
    mof_score,
    pore_selectivity,
    quantum_coherence_factor,
    temp_correction,
)
from .base import AdapterConfig, AnalysisResult, BaseAdapter


def _clamp_efficiency(eta: float) -> float:
    """Clamp efficiency to (0, 1] for valid D-space transform."""
    return max(1e-10, min(eta, 1.0))


class PhotosynthesisAdapter(BaseAdapter):
    """Artificial photosynthesis analysis via D-space linearisation.

    Input data format depends on ``mode``:

    **cascade** (default)::

        {"mode": "cascade",
         "steps": [{"name": str, "efficiency": float}, ...],
         "temperature_c": 25, "co2_ppm": 415,
         "target_efficiency": 0.20}

    **mof_filter**::

        {"mode": "mof_filter",
         "candidates": ["ZIF-8", "MOF-74-Mg", ...],
         "constraints": {"abundant_only": true, "max_cost_relative": 2.0,
                         "min_selectivity": 50, "self_healing": false}}

    **full_system** (combines cascade + MOF + coherence)::

        {"mode": "full_system",
         "steps": [...], "mof": "MOF-74-Mg",
         "coherence_coupling": 0.8,
         "temperature_c": 25, "co2_ppm": 415,
         "solar_irradiance_w_m2": 1000, "unit_area_m2": 1.0}
    """

    def __init__(self, config: AdapterConfig | None = None) -> None:
        if config is None:
            config = AdapterConfig(
                name="photosynthesis",
                version="0.1.0",
                description=(
                    "Artificial photosynthesis, MOF filters, "
                    "and quantum coherence via D-space"
                ),
            )
        super().__init__(config)
        self._validator = SumRuleValidator()

    # ------------------------------------------------------------------
    # ingest
    # ------------------------------------------------------------------
    def ingest(self, raw_data: dict) -> dict:
        mode = raw_data.get("mode", "cascade")
        temp_c = float(raw_data.get("temperature_c", 25.0))
        co2_ppm = float(raw_data.get("co2_ppm", 415.0))

        if mode == "cascade":
            return self._ingest_cascade(raw_data, temp_c, co2_ppm)
        if mode == "mof_filter":
            return self._ingest_mof(raw_data)
        if mode == "full_system":
            return self._ingest_full(raw_data, temp_c, co2_ppm)
        return {"error": f"Unknown mode '{mode}'"}

    def _ingest_cascade(self, raw: dict, temp_c: float,
                        co2_ppm: float) -> dict:
        steps = raw.get("steps", NATURAL_STEPS)
        target = float(raw.get("target_efficiency", 0.20))

        d_steps: list[dict] = []
        product = 1.0
        for s in steps:
            eta = _clamp_efficiency(float(s.get("efficiency", 0.5)))
            d_val = D(eta)
            product *= eta
            d_steps.append({
                "name": s.get("name", "unnamed"),
                "efficiency": eta,
                "d_value": d_val,
                "catalyst": s.get("catalyst", ""),
            })

        return {
            "mode": "cascade",
            "steps": d_steps,
            "overall_efficiency": product,
            "d_overall": D(max(product, 1e-10)),
            "target_efficiency": target,
            "d_target": D(max(target, 1e-10)),
            "temperature_c": temp_c,
            "co2_ppm": co2_ppm,
            "temp_factor": temp_correction(temp_c),
            "co2_sat": co2_factor(co2_ppm),
        }

    def _ingest_mof(self, raw: dict) -> dict:
        candidates = raw.get("candidates", list(MOF_MATERIALS.keys()))
        constraints = raw.get("constraints", {})

        entries: list[dict] = []
        for name in candidates:
            mat = MOF_MATERIALS.get(name)
            if mat is None:
                continue
            score = mof_score(mat)
            pore_phi = abs(mat["pore_nm"] - PHI_OPTIMAL_PORE_NM)
            geo_sel = pore_selectivity(mat["pore_nm"])
            entries.append({
                "name": name,
                **mat,
                "score": score,
                "d_score": D(max(score, 1e-10)),
                "pore_phi_match": pore_phi,
                "geometric_selectivity": geo_sel,
            })

        return {
            "mode": "mof_filter",
            "candidates": entries,
            "constraints": constraints,
        }

    def _ingest_full(self, raw: dict, temp_c: float,
                     co2_ppm: float) -> dict:
        cascade_data = self._ingest_cascade(raw, temp_c, co2_ppm)
        mof_name = raw.get("mof", "Fe-BTC")
        mof_entry = MOF_MATERIALS.get(mof_name, {})
        coupling = float(raw.get("coherence_coupling", 0.8))
        irradiance = float(raw.get("solar_irradiance_w_m2", 1000.0))
        area = float(raw.get("unit_area_m2", 1.0))

        coherence = quantum_coherence_factor(temp_c, coupling)
        score = mof_score(mof_entry) if mof_entry else 0.0

        return {
            "mode": "full_system",
            "cascade": cascade_data,
            "mof_name": mof_name,
            "mof_entry": mof_entry,
            "mof_score": score,
            "coherence_coupling": coupling,
            "coherence_factor": coherence,
            "solar_irradiance_w_m2": irradiance,
            "unit_area_m2": area,
            "temperature_c": temp_c,
            "co2_ppm": co2_ppm,
        }

    # ------------------------------------------------------------------
    # analyze
    # ------------------------------------------------------------------
    def analyze(self, d_data: dict) -> AnalysisResult:
        if "error" in d_data:
            return AnalysisResult(
                success=False, data=d_data, d_space_values=[],
                consistency_score=0.0, hierarchy=[],
                recommendations=[d_data["error"]],
            )
        mode = d_data["mode"]
        if mode == "cascade":
            return self._analyze_cascade(d_data)
        if mode == "mof_filter":
            return self._analyze_mof(d_data)
        if mode == "full_system":
            return self._analyze_full(d_data)
        return AnalysisResult(
            success=False, data=d_data, d_space_values=[],
            consistency_score=0.0, hierarchy=[],
            recommendations=[f"Unknown mode '{mode}'"],
        )

    def _analyze_cascade(self, d_data: dict) -> AnalysisResult:
        steps = d_data["steps"]
        d_overall = d_data["d_overall"]
        target = d_data["target_efficiency"]
        d_target = d_data["d_target"]

        # D-values and sum-rule
        d_values = [s["d_value"] for s in steps]
        d_sum = sum(d_values)
        sr = self._validator.validate(
            d_values, d_overall, tolerance_ppm=100,
        )
        consistency = max(0.0, 1.0 - sr["deviation_ppm"] / 1e6)

        # Contribution percentages
        for s in steps:
            s["contribution_pct"] = (
                (s["d_value"] / d_sum * 100) if d_sum > 0 else 0
            )

        # Bottleneck = highest D-value (lowest efficiency)
        bottleneck = max(steps, key=lambda s: s["d_value"])

        # Gap to target
        d_gap = d_target - d_overall
        improvements: list[str] = []
        if d_gap < 0:
            # Need to reduce D-sum (increase efficiencies)
            gap_abs = abs(d_gap)
            # Suggest improving the worst step
            improvements.append(
                f"Reduce D({bottleneck['name']}) by "
                f"{gap_abs:.3f} (from {bottleneck['d_value']:.3f} to "
                f"{bottleneck['d_value'] - gap_abs:.3f}, "
                f"i.e. raise efficiency to "
                f"{x_from_D(bottleneck['d_value'] - gap_abs):.3f})"
            )

        # Recommendations
        recs = self._cascade_recommendations(
            steps, bottleneck, d_data, d_gap,
        )

        return AnalysisResult(
            success=True,
            data={
                "overall_efficiency": d_data["overall_efficiency"],
                "d_overall": d_overall,
                "step_analysis": steps,
                "bottleneck": {
                    "step_name": bottleneck["name"],
                    "d_value": bottleneck["d_value"],
                    "efficiency": bottleneck["efficiency"],
                    "contribution_pct": bottleneck["contribution_pct"],
                    "catalyst": bottleneck.get("catalyst", ""),
                },
                "sum_rule": sr,
                "gap_to_target": {
                    "target": target,
                    "d_target": d_target,
                    "d_gap": d_gap,
                    "improvements_needed": improvements,
                },
                "env_corrections": {
                    "temp_factor": d_data["temp_factor"],
                    "co2_saturation": d_data["co2_sat"],
                },
            },
            d_space_values=d_values,
            consistency_score=consistency,
            hierarchy=[
                {"step": s["name"], "d_value": s["d_value"],
                 "rank": i + 1}
                for i, s in enumerate(
                    sorted(steps, key=lambda s: -s["d_value"])
                )
            ],
            recommendations=recs,
        )

    def _cascade_recommendations(
        self, steps: list[dict], bottleneck: dict,
        d_data: dict, d_gap: float,
    ) -> list[str]:
        recs: list[str] = []
        bn_name = bottleneck["name"]

        if bn_name == "carbon_fixation":
            recs.append(
                "Carbon fixation (RuBisCO) is the bottleneck at D="
                f"{bottleneck['d_value']:.3f}. Consider engineered "
                "RuBisCO variants or C4/CAM carbon concentrating "
                "mechanisms to improve specificity."
            )
        elif bn_name == "photorespiration":
            recs.append(
                "Photorespiration wastes energy. Engineering RuBisCO "
                "with higher CO2/O2 specificity or encapsulating in "
                "carboxysomes can suppress this pathway."
            )
        elif bn_name == "water_splitting":
            recs.append(
                "Water splitting catalyst (Mn4CaO5 mimic) limits "
                "efficiency. Explore Co-Pi or Ir-oxide catalysts "
                "for artificial OEC with higher turnover."
            )
        else:
            recs.append(
                f"Step '{bn_name}' is the primary bottleneck "
                f"(D={bottleneck['d_value']:.3f}). Focus R&D here "
                "for maximum system improvement."
            )

        if d_gap < 0:
            recs.append(
                f"Target efficiency ({d_data['target_efficiency']:.1%}) "
                f"requires D-reduction of {abs(d_gap):.3f}. "
                "This is achievable by improving 1-2 bottleneck steps."
            )

        if d_data["co2_sat"] < 0.8:
            recs.append(
                f"CO2 saturation is only {d_data['co2_sat']:.1%} at "
                f"{d_data['co2_ppm']:.0f} ppm. Consider CO2 "
                "concentrating (MOF pre-filter) or point-source capture."
            )

        if d_data["temp_factor"] < 0.9:
            recs.append(
                f"Temperature correction factor {d_data['temp_factor']:.3f}"
                " indicates suboptimal conditions. Target 20-30 C range."
            )

        return recs

    def _analyze_mof(self, d_data: dict) -> AnalysisResult:
        candidates = d_data["candidates"]
        constraints = d_data["constraints"]

        # Apply constraints
        filtered = list(candidates)
        if constraints.get("abundant_only", False):
            filtered = [c for c in filtered if c.get("abundant", False)]
        max_cost = constraints.get("max_cost_relative")
        if max_cost is not None:
            filtered = [
                c for c in filtered
                if c.get("cost_relative", 999) <= max_cost
            ]
        min_sel = constraints.get("min_selectivity")
        if min_sel is not None:
            filtered = [
                c for c in filtered
                if c.get("co2_n2_selectivity", 0) >= min_sel
            ]
        if constraints.get("self_healing", False):
            filtered = [
                c for c in filtered if c.get("self_healing", False)
            ]

        # Sort by score descending
        filtered.sort(key=lambda c: -c["score"])

        d_values = [c["d_score"] for c in filtered]
        consistency = 1.0 if filtered else 0.0

        recs = self._mof_recommendations(filtered, candidates, constraints)

        return AnalysisResult(
            success=True,
            data={
                "mof_ranking": [
                    {
                        "name": c["name"],
                        "score": round(c["score"], 3),
                        "d_score": round(c["d_score"], 4),
                        "pore_phi_match": round(c["pore_phi_match"], 4),
                        "geometric_selectivity": round(
                            c["geometric_selectivity"], 2
                        ),
                        "co2_capacity_mmol_g": c["co2_capacity_mmol_g"],
                        "co2_n2_selectivity": c["co2_n2_selectivity"],
                        "abundant": c.get("abundant", False),
                        "self_healing": c.get("self_healing", False),
                    }
                    for c in filtered
                ],
                "phi_optimal_pore_nm": round(PHI_OPTIMAL_PORE_NM, 4),
                "total_candidates": len(candidates),
                "after_constraints": len(filtered),
                "constraints_applied": constraints,
            },
            d_space_values=d_values,
            consistency_score=consistency,
            hierarchy=[
                {"mof": c["name"], "score": c["score"], "rank": i + 1}
                for i, c in enumerate(filtered)
            ],
            recommendations=recs,
        )

    def _mof_recommendations(
        self, filtered: list[dict], all_cands: list[dict],
        constraints: dict,
    ) -> list[str]:
        recs: list[str] = []
        if not filtered:
            recs.append(
                "No MOFs survive the applied constraints. "
                "Relax abundant_only or increase max_cost_relative."
            )
            return recs

        best = filtered[0]
        recs.append(
            f"Top candidate: {best['name']} "
            f"(score={best['score']:.1f}, "
            f"capacity={best['co2_capacity_mmol_g']} mmol/g, "
            f"selectivity={best['co2_n2_selectivity']}x)."
        )

        # PHI pore analysis
        phi_close = [
            c for c in filtered if c["pore_phi_match"] < 0.05
        ]
        if phi_close:
            names = ", ".join(c["name"] for c in phi_close)
            recs.append(
                f"PHI-optimal pore match (<0.05 nm): {names}. "
                "These approach the golden-ratio pore geometry "
                f"({PHI_OPTIMAL_PORE_NM:.3f} nm) for maximum CO2/N2 "
                "selectivity."
            )

        # Self-healing bonus
        healers = [c for c in filtered if c.get("self_healing")]
        if healers:
            names = ", ".join(c["name"] for c in healers)
            recs.append(
                f"Self-healing MOFs: {names}. "
                "These regenerate under cycling, reducing replacement "
                "cost and enabling circular-economy operation."
            )

        if len(filtered) < len(all_cands):
            removed = len(all_cands) - len(filtered)
            recs.append(
                f"{removed} candidate(s) removed by constraints. "
                "Review constraint strictness if more options needed."
            )

        return recs

    def _analyze_full(self, d_data: dict) -> AnalysisResult:
        cascade = d_data["cascade"]
        cascade_result = self._analyze_cascade(cascade)
        cascade_eff = cascade["overall_efficiency"]

        temp_c = d_data["temperature_c"]
        co2_ppm = d_data["co2_ppm"]
        coherence = d_data["coherence_factor"]
        temp_fac = temp_correction(temp_c)
        co2_sat = co2_factor(co2_ppm)

        # MOF capture effectiveness (normalised 0-1)
        mof_name = d_data["mof_name"]
        mof_entry = d_data["mof_entry"]
        mof_cap = mof_entry.get("co2_capacity_mmol_g", 0.0) if mof_entry else 0.0
        # Normalise capacity to 0-1 (10 mmol/g = excellent)
        mof_eff = min(mof_cap / 10.0, 1.0)

        # System efficiency = cascade * mof * coherence * env corrections
        eta_system = (
            cascade_eff * mof_eff * coherence
            * temp_fac * co2_sat
        )
        eta_system = max(eta_system, 1e-10)
        d_system = D(eta_system)

        # CO2 captured per m2 per day (rough estimate)
        # Solar constant 1000 W/m2, 12 hr sunshine, 6 mol CO2 per mol glucose
        # 1 mol glucose = 48 photons * ~2 eV = ~15.4 MJ
        irradiance = d_data["solar_irradiance_w_m2"]
        area = d_data["unit_area_m2"]
        sunshine_hours = 12.0
        energy_j = irradiance * area * sunshine_hours * 3600  # J/day
        # CO2 fixed: energy * efficiency / (2870 kJ/mol glucose) * 6 mol CO2
        # * 44 g/mol CO2 -> kg
        co2_mol_day = (
            energy_j * eta_system / (2870e3) * 6.0
        )
        co2_kg_day = co2_mol_day * 0.044  # 44 g/mol

        # Subsystem D-values for bottleneck analysis
        subsystems = [
            {"name": "cascade", "efficiency": cascade_eff,
             "d_value": D(max(cascade_eff, 1e-10))},
            {"name": "mof_capture", "efficiency": mof_eff,
             "d_value": D(max(mof_eff, 1e-10))},
            {"name": "coherence", "efficiency": coherence,
             "d_value": D(max(coherence, 1e-10))},
            {"name": "temperature", "efficiency": temp_fac,
             "d_value": D(max(temp_fac, 1e-10))},
            {"name": "co2_saturation", "efficiency": co2_sat,
             "d_value": D(max(co2_sat, 1e-10))},
        ]
        system_bottleneck = max(subsystems, key=lambda s: s["d_value"])

        d_values = [s["d_value"] for s in subsystems]
        sr = self._validator.validate(d_values, d_system, tolerance_ppm=1000)
        consistency = max(0.0, 1.0 - sr["deviation_ppm"] / 1e6)

        recs = self._full_recommendations(
            subsystems, system_bottleneck, eta_system, co2_kg_day,
            mof_name, d_data,
        )

        return AnalysisResult(
            success=True,
            data={
                "overall_efficiency": eta_system,
                "d_system": d_system,
                "co2_per_m2_day_kg": round(co2_kg_day, 6),
                "subsystems": [
                    {"name": s["name"], "efficiency": round(s["efficiency"], 6),
                     "d_value": round(s["d_value"], 4)}
                    for s in subsystems
                ],
                "bottleneck": {
                    "subsystem": system_bottleneck["name"],
                    "d_value": system_bottleneck["d_value"],
                    "efficiency": system_bottleneck["efficiency"],
                },
                "mof": {
                    "name": mof_name,
                    "score": round(d_data["mof_score"], 3),
                    "capture_efficiency": round(mof_eff, 4),
                },
                "coherence": {
                    "factor": round(coherence, 6),
                    "coupling": d_data["coherence_coupling"],
                    "temp_stable": coherence > 0.5,
                },
                "cascade_detail": cascade_result.data,
                "sum_rule": sr,
            },
            d_space_values=d_values,
            consistency_score=consistency,
            hierarchy=[
                {"subsystem": s["name"], "d_value": s["d_value"],
                 "rank": i + 1}
                for i, s in enumerate(
                    sorted(subsystems, key=lambda s: -s["d_value"])
                )
            ],
            recommendations=recs,
        )

    def _full_recommendations(
        self, subsystems: list[dict], bottleneck: dict,
        eta_system: float, co2_kg: float,
        mof_name: str, d_data: dict,
    ) -> list[str]:
        recs: list[str] = []
        bn = bottleneck["name"]

        recs.append(
            f"System efficiency: {eta_system:.4%}. "
            f"CO2 capture: {co2_kg:.4f} kg/m2/day."
        )
        recs.append(
            f"Primary bottleneck: {bn} "
            f"(D={bottleneck['d_value']:.3f}, "
            f"eff={bottleneck['efficiency']:.3f})."
        )

        if bn == "cascade":
            recs.append(
                "Photosynthesis cascade limits system. "
                "See cascade-mode analysis for per-step improvements."
            )
        elif bn == "mof_capture":
            recs.append(
                f"MOF '{mof_name}' capture rate is the bottleneck. "
                "Consider higher-capacity MOFs (MOF-74-Mg: 8.9 mmol/g) "
                "or multi-layer MOF beds."
            )
        elif bn == "coherence":
            coupling = d_data["coherence_coupling"]
            recs.append(
                f"Quantum coherence (coupling={coupling:.2f}) "
                "degrades efficiency. Increase coupling via "
                "structured light-harvesting scaffolds or lower "
                "operating temperature."
            )
        elif bn == "co2_saturation":
            recs.append(
                f"CO2 saturation at {d_data['co2_ppm']:.0f} ppm "
                "is low. Use MOF pre-concentrator to raise local "
                "CO2 partial pressure before the reaction stage."
            )

        return recs

    # ------------------------------------------------------------------
    # report
    # ------------------------------------------------------------------
    def report(self, result: AnalysisResult) -> dict:
        data = result.data
        mode = data.get("mode") or (
            "full_system" if "subsystems" in data
            else "mof_filter" if "mof_ranking" in data
            else "cascade"
        )

        base = {
            "adapter": self.config.name,
            "mode": mode,
            "success": result.success,
            "consistency_score": round(result.consistency_score, 6),
            "recommendations": result.recommendations,
        }

        if mode == "cascade":
            base.update({
                "overall_efficiency": {
                    "value": data.get("overall_efficiency"),
                    "d_value": data.get("d_overall"),
                },
                "step_analysis": data.get("step_analysis", []),
                "bottleneck": data.get("bottleneck", {}),
                "gap_to_target": data.get("gap_to_target", {}),
                "sum_rule": data.get("sum_rule", {}),
                "env_corrections": data.get("env_corrections", {}),
            })
        elif mode == "mof_filter":
            base.update({
                "mof_ranking": data.get("mof_ranking", []),
                "phi_optimal_pore_nm": data.get("phi_optimal_pore_nm"),
                "total_candidates": data.get("total_candidates"),
                "after_constraints": data.get("after_constraints"),
            })
        elif mode == "full_system":
            base.update({
                "overall_efficiency": data.get("overall_efficiency"),
                "d_system": data.get("d_system"),
                "co2_per_m2_day_kg": data.get("co2_per_m2_day_kg"),
                "subsystems": data.get("subsystems", []),
                "bottleneck": data.get("bottleneck", {}),
                "mof": data.get("mof", {}),
                "coherence": data.get("coherence", {}),
                "sum_rule": data.get("sum_rule", {}),
            })

        return base
