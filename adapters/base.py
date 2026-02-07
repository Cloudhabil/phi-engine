"""
phi_engine.adapters.base — Abstract base for vertical adapters.

Follows the Channel ABC pattern from moltbot.
Zero external dependencies.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AdapterConfig:
    """Configuration for a vertical adapter."""

    name: str
    version: str = "0.1.0"
    description: str = ""
    settings: dict = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """Standardised output from any adapter analysis."""

    success: bool
    data: dict
    d_space_values: list[float]
    consistency_score: float       # 0.0 – 1.0 (from sum-rule check)
    hierarchy: list[dict]          # Representation ranking
    recommendations: list[str]
    metadata: dict = field(default_factory=dict)


class BaseAdapter(ABC):
    """Abstract base class for vertical adapters.

    Subclasses must implement *ingest*, *analyze*, and *report*.
    """

    def __init__(self, config: AdapterConfig) -> None:
        self.config = config

    @abstractmethod
    def ingest(self, raw_data: dict) -> dict:
        """Transform raw domain data into D-space representation."""

    @abstractmethod
    def analyze(self, d_data: dict) -> AnalysisResult:
        """Run PHI-engine analysis on D-space data."""

    @abstractmethod
    def report(self, result: AnalysisResult) -> dict:
        """Generate domain-specific report from analysis result."""
