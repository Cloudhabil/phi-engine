"""
phi_engine.analyzer — Sum-rule validation, representation decomposition,
consistency checking.

Zero external dependencies.
"""
from __future__ import annotations

from math import pi

from .core import (
    D,
    Energy,
    fib,
    mirror,
)


# ---------------------------------------------------------------------------
# Sum-Rule Validator
# ---------------------------------------------------------------------------
class SumRuleValidator:
    """Validates that correction coefficients satisfy algebraic constraints."""

    @staticmethod
    def validate(
        c_values: list[float],
        expected_sum: float,
        tolerance_ppm: float = 100,
    ) -> dict:
        """Check whether sum(c_values) matches expected_sum within tolerance.

        Returns:
            dict with keys: valid, actual_sum, expected_sum, deviation_ppm,
            tolerance_ppm, residual.
        """
        actual = sum(c_values)
        if expected_sum == 0:
            deviation_ppm = abs(actual) * 1e6
        else:
            deviation_ppm = abs(actual - expected_sum) / abs(expected_sum) * 1e6
        return {
            "valid": deviation_ppm <= tolerance_ppm,
            "actual_sum": actual,
            "expected_sum": expected_sum,
            "deviation_ppm": round(deviation_ppm, 3),
            "tolerance_ppm": tolerance_ppm,
            "residual": round(actual - expected_sum, 12),
        }

    @staticmethod
    def find_missing(
        c_values: list[float],
        target_sum: float,
    ) -> list[float]:
        """Return the single correction term that closes the sum rule."""
        return [target_sum - sum(c_values)]


# ---------------------------------------------------------------------------
# Representation Decomposer
# ---------------------------------------------------------------------------
class RepresentationDecomposer:
    """Decomposes integers into Fibonacci products and GUT representations."""

    # Known GUT representations keyed by adjoint dimension
    KNOWN_REPS: dict[int, dict] = {
        1:   {"group": "U(1)",   "form": "F(1) = 1"},
        3:   {"group": "SU(2)",  "form": "F(4) = 3"},
        8:   {"group": "SU(3)",  "form": "F(6) = 8"},
        12:  {"group": "SM gauge", "form": "L(12) = 322 states"},
        24:  {"group": "SU(5) adj", "form": "F(5)^2 - 1 = 24"},
        45:  {"group": "SO(10) adj", "form": "F(4)^2 * F(5) = 45"},
        78:  {"group": "E6 adj",  "form": "45 + 16 + 16_bar + 1"},
        133: {"group": "E7 adj",  "form": "133 = 7 * 19"},
        248: {"group": "E8 adj",  "form": "F(6) * 31 = 248"},
    }

    @staticmethod
    def fibonacci_factors(n: int) -> dict:
        """Decompose n into products of Fibonacci numbers.

        Uses greedy factorisation with Fibonacci numbers > 1.
        Returns dict with factors list, product, and residual.
        """
        if n <= 0:
            return {"factors": [], "product": 0, "residual": n}

        # Collect unique Fibonacci numbers > 1 up to n
        fibs: list[int] = []
        seen: set[int] = set()
        k = 3  # fib(3)=2, skip fib(0)=0, fib(1)=1, fib(2)=1
        while True:
            f = fib(k)
            if f > n:
                break
            if f not in seen:
                fibs.append(f)
                seen.add(f)
            k += 1
        fibs.sort(reverse=True)

        factors: list[int] = []
        remaining = n
        for f in fibs:
            while remaining > 1 and remaining % f == 0:
                factors.append(f)
                remaining //= f
        factors.sort()
        product = 1
        for f in factors:
            product *= f
        return {
            "factors": factors,
            "product": product,
            "residual": n - product,
            "exact": product == n,
        }

    @classmethod
    def gut_decomposition(cls, parent_dim: int) -> dict:
        """Decompose a representation dimension into known GUT reps."""
        if parent_dim in cls.KNOWN_REPS:
            info = cls.KNOWN_REPS[parent_dim]
            return {
                "dimension": parent_dim,
                "group": info["group"],
                "fibonacci_form": info["form"],
                "fibonacci_factors": cls.fibonacci_factors(parent_dim),
            }
        fib_info = cls.fibonacci_factors(parent_dim)
        return {
            "dimension": parent_dim,
            "group": "unknown",
            "fibonacci_form": None,
            "fibonacci_factors": fib_info,
        }

    @classmethod
    def hierarchy_rank(cls, denominators: list[int]) -> list[dict]:
        """Rank a list of denominators by GUT significance.

        SO(10) mapping: smaller Fibonacci-divisible denominators rank higher.
        """
        ranked: list[dict] = []
        for den in denominators:
            info = cls.gut_decomposition(den)
            # Score: known rep = high, Fibonacci-exact = medium
            if info["group"] != "unknown":
                score = 3
            elif info["fibonacci_factors"]["exact"]:
                score = 2
            else:
                score = 1
            ranked.append({
                "denominator": den,
                "score": score,
                **info,
            })
        ranked.sort(key=lambda r: (-r["score"], r["denominator"]))
        return ranked


# ---------------------------------------------------------------------------
# Consistency Checker
# ---------------------------------------------------------------------------
class ConsistencyChecker:
    """Checks D-space closure, energy conservation, mirror symmetry."""

    @staticmethod
    def d_space_closure(x: float, tolerance: float = 1e-10) -> dict:
        """Verify D(x) + D(1/x) = 0 (closure property)."""
        if x <= 0:
            return {"valid": False, "error": "x must be > 0"}
        d_x = D(x)
        d_inv = D(1.0 / x)
        residual = d_x + d_inv
        return {
            "valid": abs(residual) < tolerance,
            "D_x": d_x,
            "D_inv_x": d_inv,
            "residual": residual,
        }

    @staticmethod
    def energy_conservation(x: float, tolerance: float = 1e-10) -> dict:
        """Verify E(x) = 2*PI (energy conservation law)."""
        if x <= 0:
            return {"valid": False, "error": "x must be > 0"}
        e = Energy(x)
        expected = 2 * pi
        residual = e - expected
        return {
            "valid": abs(residual) < tolerance,
            "energy": e,
            "expected": expected,
            "residual": residual,
        }

    @staticmethod
    def mirror_symmetry(values: list[int]) -> dict:
        """Verify M(M(x)) = x for all values (involution check)."""
        results: list[dict] = []
        all_valid = True
        for v in values:
            m = mirror(v)
            mm = mirror(m)
            valid = mm == v
            if not valid:
                all_valid = False
            results.append({"value": v, "mirror": m, "mirror_mirror": mm, "valid": valid})
        return {"all_valid": all_valid, "checks": results}

    @classmethod
    def full_check(cls, x: float) -> dict:
        """Run all consistency checks on a single value."""
        return {
            "d_space_closure": cls.d_space_closure(x),
            "energy_conservation": cls.energy_conservation(x),
        }
