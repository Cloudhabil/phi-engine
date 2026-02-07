"""
phi_engine — Zero-parameter algebraic prediction engine based on PHI.

Public API::

    from phi_engine import PhiEngine
    engine = PhiEngine()
    engine.transform([0.5, 1.0, 2.0])
    engine.decompose(45)
    engine.validate([-1, 1, 2, 0.5], 2.5)

Core constants::

    from phi_engine import PHI, OMEGA, BETA, GAMMA
    from phi_engine import D, x_from_D, Theta, Energy
    from phi_engine import fib, lucas, mirror
"""
from .core import (
    ALPHA,
    ALPHA_EM,
    BETA,
    BRAHIM_NUMBERS,
    DIMENSION_NAMES,
    DIMENSION_SILICON,
    ENERGY_CONSTANT,
    FIBONACCI_PRIMES,
    GAMMA,
    GENESIS_CONSTANT,
    LUCAS_NUMBERS,
    MIRROR_CONSTANT,
    OMEGA,
    PHI,
    TOTAL_STATES,
    D,
    D_complex,
    Energy,
    Energy_complex,
    Theta,
    fib,
    lucas,
    mirror,
    x_from_D,
)
from .engine import PhiEngine
from .photosynthesis_constants import (
    MOF_MATERIALS,
    NATURAL_OVERALL,
    NATURAL_STEPS,
    co2_factor,
    mof_score,
    photon_energy_eV,
    pore_selectivity,
    temp_correction,
)

__version__ = "1.618.0"

__all__ = [
    # Engine
    "PhiEngine",
    # Constants
    "PHI",
    "ALPHA",
    "OMEGA",
    "BETA",
    "GAMMA",
    "ALPHA_EM",
    "GENESIS_CONSTANT",
    "ENERGY_CONSTANT",
    "BRAHIM_NUMBERS",
    "MIRROR_CONSTANT",
    "LUCAS_NUMBERS",
    "TOTAL_STATES",
    "FIBONACCI_PRIMES",
    "DIMENSION_NAMES",
    "DIMENSION_SILICON",
    # Photosynthesis
    "NATURAL_STEPS",
    "NATURAL_OVERALL",
    "MOF_MATERIALS",
    "photon_energy_eV",
    "temp_correction",
    "co2_factor",
    "mof_score",
    "pore_selectivity",
    # Functions
    "D",
    "x_from_D",
    "Theta",
    "Energy",
    "D_complex",
    "Energy_complex",
    "fib",
    "lucas",
    "mirror",
]
