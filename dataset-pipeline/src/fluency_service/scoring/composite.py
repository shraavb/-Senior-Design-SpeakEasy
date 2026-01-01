"""
Composite fluency score calculator.

Combines all analyzer metrics into a single fluency score with configurable weights.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..config import AnalyzerWeights, CEFRThresholds


def calculate_composite_score(
    metrics: Any,  # MetricsBreakdown
    weights: Optional[AnalyzerWeights] = None,
) -> float:
    """
    Calculate weighted composite fluency score.

    Formula:
    FLUENCY_SCORE = (
        0.25 × Pronunciation_Accuracy +
        0.20 × Temporal_Metrics +
        0.15 × Lexical_Accuracy +
        0.20 × (100 - Disfluency_Score) +  # Inverse: fewer disfluencies = higher
        0.10 × Prosodic_Quality +
        0.10 × Communicative_Competence
    )

    Args:
        metrics: MetricsBreakdown object with all analyzer results
        weights: Optional custom weights (defaults to standard weights)

    Returns:
        Composite fluency score (0-100)
    """
    if weights is None:
        weights = AnalyzerWeights()

    # Extract scores from metrics
    pronunciation = _get_score(metrics.pronunciation_accuracy)
    temporal = _get_score(metrics.temporal_metrics)
    lexical = _get_score(metrics.lexical_accuracy)
    disfluency = _get_score(metrics.disfluency_detection)
    prosodic = _get_score(metrics.prosodic_quality)
    communicative = _get_score(metrics.communicative_competence)

    # Invert disfluency score (lower disfluency = higher fluency)
    disfluency_inverted = 100 - disfluency

    # Calculate weighted sum
    score = (
        weights.pronunciation * pronunciation +
        weights.temporal * temporal +
        weights.lexical * lexical +
        weights.disfluency * disfluency_inverted +
        weights.prosodic * prosodic +
        weights.communicative * communicative
    )

    return max(0.0, min(100.0, score))


def _get_score(metric_obj: Any) -> float:
    """Extract score from metric object."""
    if hasattr(metric_obj, 'score'):
        return metric_obj.score
    elif isinstance(metric_obj, dict):
        return metric_obj.get('score', 50.0)
    return 50.0


def calculate_level_adjusted_score(
    raw_score: float,
    user_level: str = "B1",
) -> float:
    """
    Adjust score based on user's CEFR level.

    Higher levels have stricter expectations.

    Args:
        raw_score: Raw composite score (0-100)
        user_level: User's CEFR level (A1-C2)

    Returns:
        Level-adjusted score
    """
    # Level-specific adjustments
    # At lower levels, we're more lenient; at higher levels, more strict
    adjustments = {
        "A1": 10,   # Bonus for beginners
        "A2": 5,
        "B1": 0,    # Baseline
        "B2": -5,   # Stricter for upper-intermediate
        "C1": -10,  # Even stricter for advanced
        "C2": -15,  # Most strict for mastery
    }

    adjustment = adjustments.get(user_level, 0)
    adjusted = raw_score + adjustment

    return max(0.0, min(100.0, adjusted))


def get_level_assessment(
    score: float,
    thresholds: Optional[CEFRThresholds] = None,
) -> str:
    """
    Get human-readable assessment from score.

    Args:
        score: Fluency score (0-100)
        thresholds: Optional custom thresholds

    Returns:
        Assessment string: "Native-like", "Proficient", "Developing", "Needs work"
    """
    if thresholds is None:
        thresholds = CEFRThresholds()

    return thresholds.get_assessment(score)


def get_detailed_breakdown(
    metrics: Any,
    weights: Optional[AnalyzerWeights] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Get detailed score breakdown with contributions.

    Args:
        metrics: MetricsBreakdown object
        weights: Optional custom weights

    Returns:
        Dictionary with each metric's score and weighted contribution
    """
    if weights is None:
        weights = AnalyzerWeights()

    pronunciation = _get_score(metrics.pronunciation_accuracy)
    temporal = _get_score(metrics.temporal_metrics)
    lexical = _get_score(metrics.lexical_accuracy)
    disfluency = _get_score(metrics.disfluency_detection)
    prosodic = _get_score(metrics.prosodic_quality)
    communicative = _get_score(metrics.communicative_competence)

    disfluency_inverted = 100 - disfluency

    return {
        "pronunciation_accuracy": {
            "raw_score": pronunciation,
            "weight": weights.pronunciation,
            "contribution": pronunciation * weights.pronunciation,
        },
        "temporal_metrics": {
            "raw_score": temporal,
            "weight": weights.temporal,
            "contribution": temporal * weights.temporal,
        },
        "lexical_accuracy": {
            "raw_score": lexical,
            "weight": weights.lexical,
            "contribution": lexical * weights.lexical,
        },
        "disfluency_detection": {
            "raw_score": disfluency,
            "inverted_score": disfluency_inverted,
            "weight": weights.disfluency,
            "contribution": disfluency_inverted * weights.disfluency,
        },
        "prosodic_quality": {
            "raw_score": prosodic,
            "weight": weights.prosodic,
            "contribution": prosodic * weights.prosodic,
        },
        "communicative_competence": {
            "raw_score": communicative,
            "weight": weights.communicative,
            "contribution": communicative * weights.communicative,
        },
    }
