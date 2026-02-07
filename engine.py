"""
phi_engine.engine — PhiEngine facade.

Main entry point that composes core, analyzer, ladder, constants_db,
and registered adapters into a single API.  Zero external dependencies.
"""
from __future__ import annotations

from .analyzer import ConsistencyChecker, RepresentationDecomposer, SumRuleValidator
from .constants_db import ConstantsDB
from .core import D, Energy, PHI, Theta, x_from_D
from .ladder import PhiLadder

# Type-only import for adapters — avoids circular import at runtime
try:
    from .adapters.base import BaseAdapter
except Exception:  # pragma: no cover — optional
    BaseAdapter = None  # type: ignore[assignment,misc]


class PhiEngine:
    """Zero-parameter algebraic prediction engine.

    Usage::

        engine = PhiEngine()
        engine.transform([0.5, 1.0, 2.0])
        engine.decompose(45)
        engine.validate([-1, 1, 2, 0.5], 2.5)
    """

    def __init__(self) -> None:
        self.ladder = PhiLadder()
        self.constants = ConstantsDB()
        self._validator = SumRuleValidator()
        self._decomposer = RepresentationDecomposer()
        self._checker = ConsistencyChecker()
        self._adapters: dict[str, object] = {}

    # ------------------------------------------------------------------
    # D-space transforms
    # ------------------------------------------------------------------
    def transform(self, values: list[float]) -> list[float]:
        """Map raw values to D-space."""
        return [D(v) for v in values]

    def inverse_transform(self, d_values: list[float]) -> list[float]:
        """Map D-space back to values."""
        return [x_from_D(d) for d in d_values]

    def phase(self, values: list[float]) -> list[float]:
        """Compute phase Theta for each value."""
        return [Theta(v) for v in values]

    def energy(self, values: list[float]) -> list[float]:
        """Compute energy for each value (always 2*pi)."""
        return [Energy(v) for v in values]

    # ------------------------------------------------------------------
    # PHI-power mapping
    # ------------------------------------------------------------------
    def scale_map(self, n: int) -> dict:
        """Map dimension n to energy scale via PHI^n."""
        return {
            "n": n,
            "phi_power": PHI ** n,
            "energy_GeV": self.ladder.energy_GeV(n),
            "x_from_D": x_from_D(n),
        }

    # ------------------------------------------------------------------
    # Sum-rule validation
    # ------------------------------------------------------------------
    def validate(
        self,
        coefficients: list[float],
        expected_sum: float,
        tolerance_ppm: float = 100,
    ) -> dict:
        """Validate correction coefficients against sum rule."""
        return self._validator.validate(coefficients, expected_sum, tolerance_ppm)

    # ------------------------------------------------------------------
    # Representation decomposition
    # ------------------------------------------------------------------
    def decompose(self, dim: int) -> dict:
        """Fibonacci-decompose a representation dimension."""
        return self._decomposer.gut_decomposition(dim)

    def hierarchy(self, denominators: list[int]) -> list[dict]:
        """Rank denominators by GUT significance."""
        return self._decomposer.hierarchy_rank(denominators)

    # ------------------------------------------------------------------
    # Consistency
    # ------------------------------------------------------------------
    def check(self, x: float) -> dict:
        """Run full consistency check (D-closure + energy conservation)."""
        return self._checker.full_check(x)

    # ------------------------------------------------------------------
    # Adapter management
    # ------------------------------------------------------------------
    def register_adapter(self, name: str, adapter: object) -> None:
        """Register a vertical adapter by name."""
        self._adapters[name] = adapter

    def list_adapters(self) -> list[str]:
        """Return names of registered adapters."""
        return list(self._adapters)

    def run(self, adapter_name: str, data: dict) -> dict:
        """Execute analysis through a registered adapter."""
        adapter = self._adapters.get(adapter_name)
        if adapter is None:
            return {"error": f"Adapter '{adapter_name}' not registered"}
        ingested = adapter.ingest(data)  # type: ignore[attr-defined]
        result = adapter.analyze(ingested)  # type: ignore[attr-defined]
        return adapter.report(result)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Full report
    # ------------------------------------------------------------------
    def report(self, data: dict, adapter_name: str | None = None) -> dict:
        """Generate full analysis report with consistency scores."""
        values = data.get("values", [])
        result: dict = {
            "engine": "phi-engine",
            "version": "1.618.0",
        }
        if values:
            d_values = self.transform(values)
            result["d_space"] = d_values
            result["energies"] = self.energy(values)
            checks = [self._checker.full_check(v) for v in values if v > 0]
            all_valid = all(
                c["d_space_closure"]["valid"] and c["energy_conservation"]["valid"]
                for c in checks
            )
            result["consistency"] = {
                "all_valid": all_valid,
                "checks_run": len(checks),
            }
        if adapter_name and adapter_name in self._adapters:
            result["adapter_result"] = self.run(adapter_name, data)
        return result
