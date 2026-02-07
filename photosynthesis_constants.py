"""
phi_engine.photosynthesis_constants — Science constants for artificial
photosynthesis, MOF filter design, and quantum coherence modelling.

Zero external dependencies (stdlib math only).

Six sections:
  A. Photon & PAR constants
  B. Natural photosynthesis quantum yields (7 steps)
  C. MOF material database (8 entries)
  D. Molecular kinetic diameters
  E. Redox potentials & energy budget
  F. Helper functions (temp, CO2, scoring, coherence)
"""
from __future__ import annotations

from math import exp

from .core import BETA, GAMMA, PHI, D

# ===================================================================
# A. Photon & PAR Constants
# ===================================================================
PLANCK_EV_NM: float = 1239.842  # h*c in eV*nm

# Reaction centre wavelengths (nm)
P680_NM: float = 680.0  # Photosystem II
P700_NM: float = 700.0  # Photosystem I

# Photosynthetically Active Radiation range
PAR_MIN_NM: float = 400.0
PAR_MAX_NM: float = 700.0


def photon_energy_eV(wavelength_nm: float) -> float:
    """Energy of a single photon at *wavelength_nm* in electron-volts."""
    if wavelength_nm <= 0:
        raise ValueError("wavelength must be > 0")
    return PLANCK_EV_NM / wavelength_nm


# ===================================================================
# B. Natural Photosynthesis — Quantum Yield Steps
# ===================================================================
# Each step: name, efficiency (0 < eta <= 1), catalyst description.
NATURAL_STEPS: list[dict] = [
    {"name": "photon_capture",    "efficiency": 0.95,
     "catalyst": "Chlorophyll a/b antenna"},
    {"name": "charge_separation", "efficiency": 0.99,
     "catalyst": "P680/P700 reaction centres"},
    {"name": "electron_transport", "efficiency": 0.85,
     "catalyst": "Plastoquinone chain"},
    {"name": "water_splitting",   "efficiency": 0.80,
     "catalyst": "Mn4CaO5 cluster (OEC)"},
    {"name": "nadph_atp",         "efficiency": 0.66,
     "catalyst": "ATP synthase / Fd-NADP+ reductase"},
    {"name": "carbon_fixation",   "efficiency": 0.45,
     "catalyst": "RuBisCO (Calvin cycle)"},
    {"name": "photorespiration",  "efficiency": 0.72,
     "catalyst": "RuBisCO oxygenase side-reaction"},
]

# Overall = product of all step efficiencies
NATURAL_OVERALL: float = 1.0
for _step in NATURAL_STEPS:
    NATURAL_OVERALL *= _step["efficiency"]
# ~0.1424

D_NATURAL_OVERALL: float = D(NATURAL_OVERALL)
# ~4.130 (sum of individual D-values by sum rule)

# ===================================================================
# C. MOF Material Database
# ===================================================================
MOF_MATERIALS: dict[str, dict] = {
    "ZIF-8": {
        "metal": "Zn", "linker": "2-methylimidazole",
        "pore_nm": 0.34, "co2_capacity_mmol_g": 1.2,
        "co2_n2_selectivity": 15.0, "thermal_stability_c": 550.0,
        "water_stable": True, "abundant": True,
        "cost_relative": 1.0, "self_healing": False,
    },
    "MOF-74-Mg": {
        "metal": "Mg", "linker": "2,5-dihydroxyterephthalic acid",
        "pore_nm": 1.1, "co2_capacity_mmol_g": 8.9,
        "co2_n2_selectivity": 175.0, "thermal_stability_c": 300.0,
        "water_stable": False, "abundant": True,
        "cost_relative": 1.8, "self_healing": False,
    },
    "HKUST-1": {
        "metal": "Cu", "linker": "1,3,5-benzenetricarboxylic acid",
        "pore_nm": 0.9, "co2_capacity_mmol_g": 4.2,
        "co2_n2_selectivity": 22.0, "thermal_stability_c": 280.0,
        "water_stable": False, "abundant": True,
        "cost_relative": 1.5, "self_healing": False,
    },
    "UiO-66": {
        "metal": "Zr", "linker": "1,4-benzenedicarboxylic acid",
        "pore_nm": 0.6, "co2_capacity_mmol_g": 2.3,
        "co2_n2_selectivity": 30.0, "thermal_stability_c": 540.0,
        "water_stable": True, "abundant": False,
        "cost_relative": 2.5, "self_healing": False,
    },
    "MIL-101": {
        "metal": "Cr", "linker": "terephthalic acid",
        "pore_nm": 2.9, "co2_capacity_mmol_g": 5.0,
        "co2_n2_selectivity": 10.0, "thermal_stability_c": 350.0,
        "water_stable": True, "abundant": False,
        "cost_relative": 2.0, "self_healing": False,
    },
    "Mg-MOF-74": {
        "metal": "Mg", "linker": "2,5-dioxidoterephthalate",
        "pore_nm": 1.1, "co2_capacity_mmol_g": 8.0,
        "co2_n2_selectivity": 150.0, "thermal_stability_c": 310.0,
        "water_stable": False, "abundant": True,
        "cost_relative": 1.6, "self_healing": False,
    },
    "Fe-BTC": {
        "metal": "Fe", "linker": "1,3,5-benzenetricarboxylic acid",
        "pore_nm": 2.5, "co2_capacity_mmol_g": 3.1,
        "co2_n2_selectivity": 18.0, "thermal_stability_c": 370.0,
        "water_stable": True, "abundant": True,
        "cost_relative": 0.8, "self_healing": True,
    },
    "COF-300": {
        "metal": "none", "linker": "tetrahedral organic",
        "pore_nm": 0.72, "co2_capacity_mmol_g": 1.8,
        "co2_n2_selectivity": 40.0, "thermal_stability_c": 490.0,
        "water_stable": True, "abundant": True,
        "cost_relative": 1.3, "self_healing": True,
    },
}

# ===================================================================
# D. Molecular Kinetic Diameters (nm)
# ===================================================================
CO2_KINETIC_DIAMETER_NM: float = 0.330
N2_KINETIC_DIAMETER_NM: float = 0.364
O2_KINETIC_DIAMETER_NM: float = 0.346
H2O_KINETIC_DIAMETER_NM: float = 0.265
CH4_KINETIC_DIAMETER_NM: float = 0.380

# PHI-optimal pore: CO2 * PHI^0.2 ~ 0.362 nm, just under N2 (0.364).
# This is nature's golden filter — passes CO2, blocks N2.
PHI_OPTIMAL_PORE_NM: float = CO2_KINETIC_DIAMETER_NM * PHI ** 0.2

# ===================================================================
# E. Redox Potentials & Energy Budget
# ===================================================================
# Standard electrode potentials at pH 7, 25 C (volts)
E_WATER_OXIDATION_V: float = 0.82    # H2O -> O2 + 4H+ + 4e-
E_NADP_REDUCTION_V: float = -0.32    # NADP+ + H+ + 2e- -> NADPH
E_TOTAL_SPAN_V: float = E_WATER_OXIDATION_V - E_NADP_REDUCTION_V  # 1.14 V

# Glucose energy budget
PHOTONS_PER_GLUCOSE: int = 48
GLUCOSE_ENERGY_KJ_MOL: float = 2870.0  # kJ/mol combustion

# Enzyme kinetics — RuBisCO Michaelis-Menten constants
RUBISCO_KM_CO2_UM: float = 10.0    # K_M for CO2 (micro-molar)
RUBISCO_KM_O2_UM: float = 200.0    # K_M for O2 (micro-molar)
RUBISCO_SPECIFICITY: float = (
    RUBISCO_KM_O2_UM / RUBISCO_KM_CO2_UM
)  # ~20, CO2/O2 selectivity ratio

# ===================================================================
# F. Helper Functions
# ===================================================================

def temp_correction(temp_c: float) -> float:
    """Temperature correction factor with GAMMA-damped decay.

    Peaks at 25 C (plant optimum). Falls off exponentially.
    Returns a factor in (0, 1].
    """
    deviation = abs(temp_c - 25.0)
    return exp(-GAMMA * deviation)


def co2_factor(co2_ppm: float, k_half: float = 200.0) -> float:
    """Michaelis-Menten CO2 saturation factor.

    co2_factor(415) ~ 0.675 (ambient air)
    co2_factor(40000) ~ 0.995 (stack gas at 4%)
    """
    if co2_ppm < 0:
        return 0.0
    return co2_ppm / (co2_ppm + k_half)


def mof_score(entry: dict) -> float:
    """Score a MOF material for CO2 capture suitability.

    Adapted from battery_optimizer integrity formula:
    M = (capacity * selectivity * stability_norm) / cost * abundance_bonus

    Higher is better.  Returns a non-negative float.
    """
    capacity = entry.get("co2_capacity_mmol_g", 0.0)
    selectivity = entry.get("co2_n2_selectivity", 1.0)
    stability = entry.get("thermal_stability_c", 200.0) / 600.0  # normalise
    cost = max(entry.get("cost_relative", 1.0), 0.01)
    abundant = 1.5 if entry.get("abundant", False) else 1.0
    healing = 1.2 if entry.get("self_healing", False) else 1.0
    water = 1.1 if entry.get("water_stable", False) else 0.9

    raw = (capacity * selectivity * stability * abundant
           * healing * water) / cost
    return raw


def pore_selectivity(pore_nm: float) -> float:
    """Estimate CO2/N2 selectivity from pore diameter.

    Uses Gaussian selectivity centred on PHI_OPTIMAL_PORE_NM.
    Maximum selectivity ~ 200 at the phi-optimal pore.
    Falls off with distance from optimum.
    """
    max_sel = 200.0
    sigma = 0.05  # nm spread
    delta = pore_nm - PHI_OPTIMAL_PORE_NM
    return max_sel * exp(-(delta ** 2) / (2 * sigma ** 2))


def quantum_coherence_factor(temp_c: float,
                             coupling_strength: float = 1.0) -> float:
    """Quantum coherence survival at temperature *temp_c*.

    coherence = exp(-BETA * T_kelvin / (coupling * 300))

    At 25 C with coupling 1.0: ~0.79 (plants achieve this).
    Higher coupling_strength preserves coherence at higher temps.
    """
    if coupling_strength <= 0:
        return 0.0
    t_kelvin = temp_c + 273.15
    return exp(-BETA * t_kelvin / (coupling_strength * 300.0))
