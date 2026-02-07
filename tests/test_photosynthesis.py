"""Tests for photosynthesis adapter and constants."""
from phi_engine.adapters.photosynthesis import PhotosynthesisAdapter
from phi_engine.core import D
from phi_engine.engine import PhiEngine
from phi_engine.photosynthesis_constants import (
    CO2_KINETIC_DIAMETER_NM,
    MOF_MATERIALS,
    N2_KINETIC_DIAMETER_NM,
    NATURAL_OVERALL,
    NATURAL_STEPS,
    PHI_OPTIMAL_PORE_NM,
    co2_factor,
    mof_score,
    photon_energy_eV,
    pore_selectivity,
    quantum_coherence_factor,
    temp_correction,
)


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------
def test_natural_steps_count():
    assert len(NATURAL_STEPS) == 7


def test_natural_overall_product():
    product = 1.0
    for s in NATURAL_STEPS:
        product *= s["efficiency"]
    assert abs(product - NATURAL_OVERALL) < 1e-12


def test_sum_rule_conservation():
    """D(product) == sum(D(eta_i)) — the fundamental sum rule."""
    d_sum = sum(D(s["efficiency"]) for s in NATURAL_STEPS)
    d_overall = D(NATURAL_OVERALL)
    assert abs(d_sum - d_overall) < 1e-10


def test_phi_optimal_pore():
    """PHI pore sits between CO2 and N2 diameters."""
    assert PHI_OPTIMAL_PORE_NM > CO2_KINETIC_DIAMETER_NM
    assert PHI_OPTIMAL_PORE_NM < N2_KINETIC_DIAMETER_NM


def test_mof_database_entries():
    assert len(MOF_MATERIALS) == 8
    for name, mat in MOF_MATERIALS.items():
        assert "metal" in mat
        assert "pore_nm" in mat
        assert mat["co2_capacity_mmol_g"] > 0


# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------
def test_photon_energy():
    e = photon_energy_eV(680.0)
    assert 1.8 < e < 1.9  # ~1.823 eV


def test_temp_correction_optimum():
    assert temp_correction(25.0) == 1.0  # peak at 25 C


def test_temp_correction_decay():
    assert temp_correction(0.0) < 1.0
    assert temp_correction(50.0) < 1.0


def test_co2_factor_range():
    assert co2_factor(0) == 0.0
    assert 0.6 < co2_factor(415) < 0.7
    assert co2_factor(40000) > 0.99


def test_mof_score_positive():
    for name, mat in MOF_MATERIALS.items():
        assert mof_score(mat) > 0


def test_pore_selectivity_peak():
    """Maximum selectivity near the phi-optimal pore."""
    peak = pore_selectivity(PHI_OPTIMAL_PORE_NM)
    off = pore_selectivity(PHI_OPTIMAL_PORE_NM + 0.1)
    assert peak > off


def test_quantum_coherence():
    c = quantum_coherence_factor(25.0, 1.0)
    assert 0.5 < c < 1.0
    # Higher coupling preserves more coherence
    c_high = quantum_coherence_factor(25.0, 2.0)
    assert c_high > c


# ------------------------------------------------------------------
# Adapter modes
# ------------------------------------------------------------------
def _make_engine() -> PhiEngine:
    engine = PhiEngine()
    engine.register_adapter("photosynthesis", PhotosynthesisAdapter())
    return engine


def test_cascade_mode():
    engine = _make_engine()
    r = engine.run("photosynthesis", {
        "mode": "cascade",
        "steps": NATURAL_STEPS,
        "target_efficiency": 0.20,
    })
    assert r["success"]
    assert r["consistency_score"] > 0.99
    assert r["bottleneck"]["step_name"] == "carbon_fixation"
    assert len(r["recommendations"]) > 0


def test_mof_filter_mode():
    engine = _make_engine()
    r = engine.run("photosynthesis", {
        "mode": "mof_filter",
        "candidates": ["ZIF-8", "MOF-74-Mg", "Fe-BTC"],
        "constraints": {"abundant_only": True},
    })
    assert r["success"]
    assert len(r["mof_ranking"]) == 3  # all three are abundant


def test_mof_filter_constraints():
    engine = _make_engine()
    r = engine.run("photosynthesis", {
        "mode": "mof_filter",
        "candidates": list(MOF_MATERIALS.keys()),
        "constraints": {"self_healing": True},
    })
    assert r["success"]
    for m in r["mof_ranking"]:
        assert m["self_healing"]


def test_full_system_mode():
    engine = _make_engine()
    r = engine.run("photosynthesis", {
        "mode": "full_system",
        "steps": NATURAL_STEPS,
        "mof": "Fe-BTC",
        "coherence_coupling": 0.8,
        "temperature_c": 25,
        "co2_ppm": 415,
        "solar_irradiance_w_m2": 1000,
    })
    assert r["success"]
    assert r["co2_per_m2_day_kg"] > 0
    assert r["overall_efficiency"] > 0
    assert len(r["subsystems"]) == 5
    assert len(r["recommendations"]) > 0
