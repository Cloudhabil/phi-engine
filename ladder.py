"""
phi_engine.ladder — PHI-power scale mapping and energy ladder.

Maps representation dimensions to energy/scale via PHI^n.
Zero external dependencies.
"""
from __future__ import annotations

from math import log

from .core import LUCAS_NUMBERS, PHI, TOTAL_STATES, D, fib, lucas, x_from_D


class PhiLadder:
    """Maps representation dimensions to energy/scale via PHI^n."""

    # Known GUT scales: dim -> (label, Fibonacci/Lucas description)
    KNOWN_SCALES: dict[int, tuple[str, str]] = {
        1:   ("U(1) trivial", "F(1) = 1"),
        3:   ("SU(2) adjoint", "F(4) = 3"),
        8:   ("SU(3) adjoint", "F(6) = 8"),
        12:  ("SM gauge", "L(12) = 322 states"),
        24:  ("SU(5) adjoint", "F(5)^2 - 1 = 24"),
        45:  ("SO(10) adjoint", "F(4)^2 * F(5) = 45"),
        78:  ("E6 adjoint", "M_GUT"),
        133: ("E7 adjoint", "133 = 7 * 19"),
        248: ("E8 adjoint", "F(6) * 31 = 248"),
    }

    # Reference proton mass in GeV
    M_PROTON: float = 0.93827

    def phi_power(self, n: int) -> float:
        """PHI^n — fundamental scale factor."""
        return PHI ** n

    def energy_GeV(self, n: int, ref_mass: float | None = None) -> float:
        """Energy at PHI^n in GeV, anchored to proton mass."""
        m = ref_mass if ref_mass is not None else self.M_PROTON
        return m * self.phi_power(n)

    def d_space_step(self, from_scale: float, to_scale: float) -> float:
        """D-space distance between two energy scales."""
        if from_scale <= 0 or to_scale <= 0:
            raise ValueError("Scales must be > 0")
        return D(from_scale) - D(to_scale)

    def find_nearest_scale(self, value: float) -> dict:
        """Find the nearest known GUT scale to a PHI^n power."""
        if value <= 0:
            return {"error": "value must be > 0"}
        # Compute n = log(value) / log(PHI)
        n_float = log(value) / log(PHI)
        n_int = round(n_float)

        best_match = None
        best_dist = float("inf")
        for dim, (label, desc) in self.KNOWN_SCALES.items():
            dist = abs(dim - n_int)
            if dist < best_dist:
                best_dist = dist
                best_match = {"dimension": dim, "label": label, "description": desc}

        return {
            "input_value": value,
            "phi_exponent": n_float,
            "nearest_integer_n": n_int,
            "nearest_known_scale": best_match,
            "distance": best_dist,
        }

    def full_ladder(self, n_max: int = 78) -> list[dict]:
        """Generate the complete PHI-power energy ladder up to n_max."""
        ladder: list[dict] = []
        for n in range(n_max + 1):
            entry: dict = {
                "n": n,
                "phi_power": self.phi_power(n),
                "energy_GeV": self.energy_GeV(n),
                "x_from_D": x_from_D(n),
            }
            if n in self.KNOWN_SCALES:
                label, desc = self.KNOWN_SCALES[n]
                entry["label"] = label
                entry["description"] = desc
            # Add Lucas number if within 12 dimensions
            if 1 <= n <= 12:
                entry["lucas_number"] = lucas(n)
                entry["lucas_states"] = LUCAS_NUMBERS[n - 1]
            ladder.append(entry)
        return ladder

    def gut_hierarchy(self) -> list[dict]:
        """Return only the known GUT scale entries, ordered by dimension."""
        entries: list[dict] = []
        for dim in sorted(self.KNOWN_SCALES):
            label, desc = self.KNOWN_SCALES[dim]
            entries.append({
                "dimension": dim,
                "label": label,
                "description": desc,
                "phi_power": self.phi_power(dim),
                "energy_GeV": self.energy_GeV(dim),
            })
        return entries

    def alpha_gut(self) -> dict:
        """GUT coupling constant: alpha_GUT = 1/F(5)^2 = 1/25."""
        f5 = fib(5)
        return {
            "alpha_GUT": 1.0 / (f5 ** 2),
            "formula": "1/F(5)^2 = 1/25",
            "F5": f5,
        }

    def weinberg_at_gut(self) -> dict:
        """Weinberg angle at GUT scale: sin^2(theta_W) = F(4)/F(6) = 3/8."""
        f4 = fib(4)
        f6 = fib(6)
        return {
            "sin2_theta_W_gut": f4 / f6,
            "formula": "F(4)/F(6) = 3/8",
            "F4": f4,
            "F6": f6,
        }

    def total_states_check(self) -> dict:
        """Verify sum of Lucas(1..12) = 840 total states."""
        s = sum(LUCAS_NUMBERS)
        return {
            "total_states": s,
            "expected": TOTAL_STATES,
            "valid": s == TOTAL_STATES,
            "lucas_numbers": list(LUCAS_NUMBERS),
        }
