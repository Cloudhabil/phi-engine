"""
phi_engine.core — Mathematical foundation.

Deterministic constants and transforms extracted from
sovereign-pio/src/sovereign_pio/brahims_calculator.py.
Zero external dependencies (stdlib math only).
"""
from __future__ import annotations

import cmath
from math import exp, log, pi, sqrt

# ---------------------------------------------------------------------------
# Layer 1 — Core Constants
# ---------------------------------------------------------------------------
PHI: float = (1 + sqrt(5)) / 2              # 1.6180339887498949
ALPHA: float = PHI                           # Creation constant
OMEGA: float = 1 / PHI                       # 0.6180339887498949 (Return)
BETA: float = 1 / PHI**3                     # 0.2360679774997897 (Security)
GAMMA: float = 1 / PHI**4                    # 0.1458980337503155 (Damping)

GENESIS_CONSTANT: float = 2 / 901           # 0.00221975...
ENERGY_CONSTANT: float = 2 * pi             # Always conserved
BRANCH_SPACING: float = 2 * pi / log(PHI)   # ~13.0472

ALPHA_EM: float = 1 / 137.035999084         # Fine-structure constant

# ---------------------------------------------------------------------------
# Layer 4 — N-Body Manifold (Brahim Numbers)
# ---------------------------------------------------------------------------
BRAHIM_NUMBERS: tuple[int, ...] = (27, 42, 60, 75, 97, 117, 139, 154, 172, 187)
MIRROR_CONSTANT: int = 214
BRAHIM_CENTER: int = 107
BRAHIM_SUM: int = 1070

GENERATING_TRIANGLE: tuple[int, int, int] = (42, 75, 97)
MAX_CONCURRENT_AGENTS: int = 27
TOTAL_BRAHIM_SCALES: int = 369
TRIANGLE_SILICON: dict[str, int] = {"NPU": 42, "CPU": 75, "GPU": 97}

# Sequence deviations
DELTA_4: int = -3                            # SU(3) color
DELTA_5: int = 4                             # Spacetime dimensions
NET_ASYMMETRY: int = 1                       # Matter > antimatter
N_COLORS: int = 3
N_SPACETIME: int = 4
REGULATOR: int = 81                          # 3^4
BETA_0_QCD: int = 9

# Lucas numbers (dimension capacity)
LUCAS_NUMBERS: tuple[int, ...] = (1, 3, 4, 7, 11, 18, 29, 47, 76, 123, 199, 322)
TOTAL_STATES: int = 840                      # sum(LUCAS_NUMBERS)

# Fibonacci primes used in GUT decomposition
FIBONACCI_PRIMES: tuple[int, int, int] = (2, 3, 5)

# 12 dimensions to silicon
DIMENSION_SILICON: dict[int, str] = {
    1: "NPU", 2: "NPU", 3: "NPU", 4: "NPU",
    5: "CPU", 6: "CPU", 7: "CPU", 8: "CPU",
    9: "GPU", 10: "GPU", 11: "GPU", 12: "GPU",
}

DIMENSION_NAMES: tuple[str, ...] = (
    "PERCEPTION", "ATTENTION", "SECURITY", "STABILITY",
    "COMPRESSION", "HARMONY", "REASONING", "PREDICTION",
    "CREATIVITY", "WISDOM", "INTEGRATION", "UNIFICATION",
)

# Hardware bandwidth (measured 2026-01-27)
BW_NPU: float = 7.35
BW_GPU: float = 12.0
BW_RAM: float = 26.0
BW_SSD: float = 2.8


# ---------------------------------------------------------------------------
# Layer 2 — Core Transforms (DETERMINISTIC)
# ---------------------------------------------------------------------------
def D(x: float) -> float:
    """Dimension from value: D(x) = -ln(x) / ln(PHI)."""
    if x <= 0:
        raise ValueError("D(x) requires x > 0")
    return -log(x) / log(PHI)


def x_from_D(d: float) -> float:
    """Value from dimension (inverse of D): x = 1 / PHI^d."""
    return 1.0 / (PHI ** d)


def Theta(x: float) -> float:
    """Phase from value: Theta(x) = 2*PI*x."""
    return 2 * pi * x


def Energy(x: float) -> float:
    """Energy is ALWAYS 2*PI for all valid x > 0. Proven law."""
    return (PHI ** D(x)) * Theta(x)


# ---------------------------------------------------------------------------
# Layer 3 — Complex Domain
# ---------------------------------------------------------------------------
def D_complex(z: complex, k: int = 0) -> complex:
    """Complex dimension with branch index k."""
    if z == 0:
        raise ValueError("D_complex(z) requires z != 0")
    ln_z_k = cmath.log(z) + 2j * pi * k
    return -ln_z_k / log(PHI)


def Energy_complex(z: complex, k: int = 0) -> complex:
    """Complex energy: E_k(z) = PHI^D_k(z) * Theta(z)."""
    d = D_complex(z, k)
    phi_d = cmath.exp(d * log(PHI))
    return phi_d * (2 * pi * z)


# ---------------------------------------------------------------------------
# Sequences
# ---------------------------------------------------------------------------
def fib(n: int) -> int:
    """Fibonacci number F(n), 0-indexed. Iterative, handles large n."""
    if n < 0:
        raise ValueError("fib(n) requires n >= 0")
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b


def lucas(n: int) -> int:
    """Lucas number L(n), 1-indexed matching LUCAS_NUMBERS convention."""
    if 1 <= n <= len(LUCAS_NUMBERS):
        return LUCAS_NUMBERS[n - 1]
    a, b = 2, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b


def mirror(x: int) -> int:
    """Mirror operator: M(x) = 214 - x. Involution: M(M(x)) = x."""
    return MIRROR_CONSTANT - x


# ---------------------------------------------------------------------------
# NPU bandwidth model (measured)
# ---------------------------------------------------------------------------
def npu_bandwidth(n_parallel: int) -> float:
    """NPU bandwidth saturation: BW(N) = 7.20 * (1 - e^(-N/PHI)) GB/s."""
    bw_max = 7.20
    return bw_max * (1 - exp(-n_parallel / PHI))
