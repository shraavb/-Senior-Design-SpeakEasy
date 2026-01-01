"""
Base analyzer interface for fluency evaluation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AnalysisResult:
    """Standard result from any analyzer."""
    score: float  # 0-100
    details: Dict[str, Any] = field(default_factory=dict)
    errors: list = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"score": self.score}
        result.update(self.details)
        if self.errors:
            result["errors"] = self.errors
        return result


class BaseAnalyzer(ABC):
    """
    Abstract base class for fluency analyzers.

    All analyzers implement the same interface for consistent integration.
    """

    @abstractmethod
    def analyze(
        self,
        features: Any,  # AudioFeatures
        transcript: Any,  # TranscriptResult
        expected_text: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze audio features and transcript for fluency metrics.

        Args:
            features: AudioFeatures object with acoustic data
            transcript: TranscriptResult with recognized text and word timings
            expected_text: Optional ground truth text for comparison
            scenario: Optional scenario type for context-aware analysis

        Returns:
            Dictionary with 'score' (0-100) and metric-specific details
        """
        pass

    def _clamp_score(self, score: float) -> float:
        """Clamp score to valid range [0, 100]."""
        return max(0.0, min(100.0, score))

    def _safe_divide(self, numerator: float, denominator: float, default: float = 0.0) -> float:
        """Safe division with default for zero denominator."""
        if denominator == 0:
            return default
        return numerator / denominator
