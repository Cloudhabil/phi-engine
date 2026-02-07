"""phi_engine.adapters — Pluggable vertical adapters."""
from .base import AdapterConfig, AnalysisResult, BaseAdapter
from .photosynthesis import PhotosynthesisAdapter

__all__ = [
    "BaseAdapter",
    "AdapterConfig",
    "AnalysisResult",
    "PhotosynthesisAdapter",
]
