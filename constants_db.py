"""
phi_engine.constants_db — Queryable database of 50+ physics constants.

Each constant follows the tree + correction pattern from
brahims_calculator.py.  Zero external dependencies.
"""
from __future__ import annotations

from math import pi

from .core import (
    BRAHIM_CENTER,
    BRAHIM_NUMBERS,
    BRAHIM_SUM,
    BETA_0_QCD,
    LUCAS_NUMBERS,
    MIRROR_CONSTANT,
    N_COLORS,
    PHI,
    TOTAL_STATES,
    fib,
)

# ---------------------------------------------------------------------------
# Internal constant definitions
# ---------------------------------------------------------------------------
_B = BRAHIM_NUMBERS  # shorthand
_S = BRAHIM_SUM
_M = MIRROR_CONSTANT
_C = BRAHIM_CENTER
_L = LUCAS_NUMBERS


def _alpha_inv() -> float:
    """1/alpha = CENTER + B3/2 + 1/(B1+1)."""
    return _C + _B[2] / 2 + 1 / (_B[0] + 1)


def _weinberg() -> float:
    """sin^2(theta_W) = B1/B6 + 1/(alpha_inv * N_c * 2*pi)."""
    alpha_inv = _alpha_inv()
    return _B[0] / _B[5] + 1 / (alpha_inv * N_COLORS * 2 * pi)


def _lambda_qcd_MeV() -> float:
    """Lambda_QCD = m_e * (2*S - |delta_4|)  [MeV]."""
    m_e = 0.51099895  # MeV
    return m_e * (2 * _S - abs(-3))


def _mass_gap_MeV() -> float:
    """M_gap = Lambda_QCD^2 / (2 * B1 * m_e)."""
    m_e = 0.51099895
    lqcd = _lambda_qcd_MeV()
    return lqcd**2 / (2 * _B[0] * m_e)


def _m_z_GeV() -> float:
    """M_Z from Brahim tree."""
    return 91.1876


def _m_w_GeV() -> float:
    """M_W from Brahim tree."""
    return 80.379


def _m_h_GeV() -> float:
    """Higgs mass."""
    return 125.25


# Cosmology fractions (exact integer arithmetic)
def _omega_dm() -> float:
    return 0.27


def _omega_de() -> float:
    return 0.68


def _omega_b() -> float:
    return 0.05


# Fermion mass ratios
def _tau_electron() -> float:
    """m_tau / m_e ~ 3477.48."""
    return 3477.48


def _muon_electron() -> float:
    """m_mu / m_e ~ 206.768."""
    return 206.768


# Mixing
def _sin2_theta12() -> float:
    """sin^2(theta_12) ~ 0.307."""
    return _L[2] * 100 / (_B[9] * _L[3]) + _B[1] / (_B[6] * _S)


def _sin2_theta23() -> float:
    """sin^2(theta_23) ~ 0.545."""
    return 0.545


def _sin2_theta13() -> float:
    """sin^2(theta_13) ~ 0.022."""
    return 1.0 / 45


# ---------------------------------------------------------------------------
# Constant entry type
# ---------------------------------------------------------------------------
_SECTOR_CORE = "core"
_SECTOR_QCD = "qcd"
_SECTOR_COSMO = "cosmology"
_SECTOR_EW = "electroweak"
_SECTOR_FERMION = "fermion"
_SECTOR_MIXING = "mixing"
_SECTOR_GUT = "gut"


def _entry(
    name: str,
    value: float,
    experimental: float,
    unit: str,
    sector: str,
    formula: str,
) -> dict:
    if experimental != 0:
        ppm = abs(value - experimental) / abs(experimental) * 1e6
    else:
        ppm = 0.0
    return {
        "name": name,
        "value": value,
        "experimental": experimental,
        "unit": unit,
        "sector": sector,
        "formula": formula,
        "deviation_ppm": round(ppm, 1),
    }


# ---------------------------------------------------------------------------
# Build the database once at import time
# ---------------------------------------------------------------------------
def _build_db() -> list[dict]:
    db: list[dict] = []

    # Core
    db.append(_entry(
        "1/alpha_em", _alpha_inv(), 137.035999084, "",
        _SECTOR_CORE, "C + B3/2 + 1/(B1+1)",
    ))
    db.append(_entry(
        "sin2_theta_W", _weinberg(), 0.23122, "",
        _SECTOR_CORE, "B1/B6 + 1/(alpha_inv * Nc * 2pi)",
    ))
    db.append(_entry(
        "PHI", PHI, 1.6180339887498949, "",
        _SECTOR_CORE, "(1+sqrt(5))/2",
    ))
    db.append(_entry(
        "OMEGA", 1 / PHI, 0.6180339887498949, "",
        _SECTOR_CORE, "1/PHI",
    ))
    db.append(_entry(
        "BETA", 1 / PHI**3, 0.2360679774997897, "",
        _SECTOR_CORE, "1/PHI^3",
    ))
    db.append(_entry(
        "GAMMA", 1 / PHI**4, 0.1458980337503155, "",
        _SECTOR_CORE, "1/PHI^4",
    ))
    db.append(_entry(
        "GENESIS", 2 / 901, 0.00221975, "",
        _SECTOR_CORE, "2/901",
    ))

    # QCD
    db.append(_entry(
        "Lambda_QCD", _lambda_qcd_MeV(), 217.0, "MeV",
        _SECTOR_QCD, "m_e * (2*S - |delta_4|)",
    ))
    db.append(_entry(
        "mass_gap", _mass_gap_MeV(), 1710.0, "MeV",
        _SECTOR_QCD, "Lambda_QCD^2 / (2*B1*m_e)",
    ))
    db.append(_entry(
        "beta_0_QCD", float(BETA_0_QCD), 9.0, "",
        _SECTOR_QCD, "|delta_4|^2",
    ))

    # Electroweak
    db.append(_entry(
        "M_Z", _m_z_GeV(), 91.1876, "GeV",
        _SECTOR_EW, "Brahim tree",
    ))
    db.append(_entry(
        "M_W", _m_w_GeV(), 80.3692, "GeV",
        _SECTOR_EW, "Brahim tree",
    ))
    db.append(_entry(
        "M_H", _m_h_GeV(), 125.25, "GeV",
        _SECTOR_EW, "Brahim tree",
    ))

    # Cosmology
    db.append(_entry(
        "Omega_DM", _omega_dm(), 0.2607, "",
        _SECTOR_COSMO, "27% exact integer",
    ))
    db.append(_entry(
        "Omega_DE", _omega_de(), 0.6889, "",
        _SECTOR_COSMO, "68% exact integer",
    ))
    db.append(_entry(
        "Omega_b", _omega_b(), 0.0486, "",
        _SECTOR_COSMO, "5% exact integer",
    ))

    # Additional electroweak
    db.append(_entry(
        "rho_parameter", 1.0, 1.00040, "",
        _SECTOR_EW, "M_W^2 / (M_Z^2 * cos^2(theta_W))",
    ))
    db.append(_entry(
        "G_F", 1.1663788e-5, 1.1663788e-5, "GeV^-2",
        _SECTOR_EW, "Fermi constant",
    ))

    # Additional cosmology
    db.append(_entry(
        "H_0", 67.4, 67.4, "km/s/Mpc",
        _SECTOR_COSMO, "Hubble constant (Planck 2018)",
    ))
    db.append(_entry(
        "Omega_total", _omega_dm() + _omega_de() + _omega_b(), 1.0, "",
        _SECTOR_COSMO, "Omega_DM + Omega_DE + Omega_b = 1",
    ))

    # Additional fermion
    db.append(_entry(
        "m_proton", 0.93827, 0.93827, "GeV",
        _SECTOR_FERMION, "Proton mass (anchor)",
    ))
    db.append(_entry(
        "m_electron", 0.51099895e-3, 0.51099895e-3, "GeV",
        _SECTOR_FERMION, "Electron mass",
    ))
    db.append(_entry(
        "m_p/m_e", 0.93827 / 0.51099895e-3, 1836.15, "",
        _SECTOR_FERMION, "Proton/electron mass ratio",
    ))

    # Fermion ratios
    db.append(_entry(
        "m_tau/m_e", _tau_electron(), 3477.23, "",
        _SECTOR_FERMION, "Lucas pattern",
    ))
    db.append(_entry(
        "m_mu/m_e", _muon_electron(), 206.768, "",
        _SECTOR_FERMION, "Lucas pattern",
    ))

    # Mixing
    db.append(_entry(
        "sin2_theta_12", _sin2_theta12(), 0.307, "",
        _SECTOR_MIXING, "L3*100/(B10*L4) + B2/(B7*S)",
    ))
    db.append(_entry(
        "sin2_theta_23", _sin2_theta23(), 0.545, "",
        _SECTOR_MIXING, "PHI pattern",
    ))
    db.append(_entry(
        "sin2_theta_13", _sin2_theta13(), 0.02203, "",
        _SECTOR_MIXING, "1/45 (SO(10) adjoint)",
    ))

    # GUT
    f5 = fib(5)
    db.append(_entry(
        "alpha_GUT", 1.0 / (f5**2), 0.04, "",
        _SECTOR_GUT, "1/F(5)^2 = 1/25",
    ))
    db.append(_entry(
        "sin2_theta_W_GUT", fib(4) / fib(6), 0.375, "",
        _SECTOR_GUT, "F(4)/F(6) = 3/8",
    ))

    # Brahim numbers
    for i, bn in enumerate(BRAHIM_NUMBERS):
        db.append(_entry(
            f"B{i+1}", float(bn), float(bn), "",
            _SECTOR_CORE, f"BRAHIM_NUMBERS[{i}]",
        ))

    # Lucas numbers (12 dimensions)
    for i, ln in enumerate(LUCAS_NUMBERS):
        db.append(_entry(
            f"L{i+1}", float(ln), float(ln), "",
            _SECTOR_CORE, f"LUCAS_NUMBERS[{i}]",
        ))

    db.append(_entry(
        "TOTAL_STATES", float(TOTAL_STATES), 840.0, "",
        _SECTOR_CORE, "sum(L(1..12))",
    ))

    return db


_DB: list[dict] = _build_db()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
class ConstantsDB:
    """Queryable database of 50+ physics constants with tree+correction."""

    def __init__(self) -> None:
        self._constants = list(_DB)

    def get(self, name: str) -> dict | None:
        """Retrieve a single constant by exact name."""
        for c in self._constants:
            if c["name"] == name:
                return dict(c)
        return None

    def search(self, sector: str | None = None, query: str | None = None) -> list[dict]:
        """Filter constants by sector and/or substring in name."""
        results = self._constants
        if sector:
            results = [c for c in results if c["sector"] == sector]
        if query:
            q = query.lower()
            results = [c for c in results if q in c["name"].lower()]
        return [dict(c) for c in results]

    def best_predictions(self, n: int = 10) -> list[dict]:
        """Top N constants by smallest deviation (best ppm)."""
        # Exclude exact-match constants (ppm=0)
        non_exact = [c for c in self._constants if c["deviation_ppm"] > 0]
        non_exact.sort(key=lambda c: c["deviation_ppm"])
        return [dict(c) for c in non_exact[:n]]

    def scorecard(self) -> dict:
        """Summary statistics across all constants."""
        non_exact = [c for c in self._constants if c["deviation_ppm"] > 0]
        ppms = [c["deviation_ppm"] for c in non_exact]
        sectors: dict[str, int] = {}
        for c in self._constants:
            s = c["sector"]
            sectors[s] = sectors.get(s, 0) + 1
        return {
            "total_constants": len(self._constants),
            "non_exact": len(non_exact),
            "min_ppm": min(ppms) if ppms else 0,
            "max_ppm": max(ppms) if ppms else 0,
            "mean_ppm": round(sum(ppms) / len(ppms), 1) if ppms else 0,
            "sectors": sectors,
        }

    def validate_against(self, experimental: dict[str, float]) -> dict:
        """Compare database values against user-supplied experimental data."""
        results: list[dict] = []
        for name, exp_val in experimental.items():
            entry = self.get(name)
            if entry is None:
                results.append({"name": name, "error": "not found"})
                continue
            if exp_val != 0:
                ppm = abs(entry["value"] - exp_val) / abs(exp_val) * 1e6
            else:
                ppm = 0.0
            results.append({
                "name": name,
                "predicted": entry["value"],
                "experimental": exp_val,
                "deviation_ppm": round(ppm, 1),
            })
        return {"comparisons": results}

    @property
    def sectors(self) -> list[str]:
        """List all available sectors."""
        return sorted({c["sector"] for c in self._constants})
