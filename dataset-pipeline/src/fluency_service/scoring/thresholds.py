"""
Level-adjusted score thresholds for CEFR assessment.

Provides different threshold scales based on user's target CEFR level.
"""

from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class LevelThresholds:
    """Score thresholds for a specific CEFR level."""
    native_like: int = 90
    proficient: int = 75
    developing: int = 60
    needs_work: int = 0

    def get_band(self, score: float) -> str:
        """Get assessment band for score."""
        if score >= self.native_like:
            return "Native-like"
        elif score >= self.proficient:
            return "Proficient"
        elif score >= self.developing:
            return "Developing"
        else:
            return "Needs work"

    def get_band_range(self, band: str) -> Tuple[int, int]:
        """Get score range for a band."""
        ranges = {
            "Native-like": (self.native_like, 100),
            "Proficient": (self.proficient, self.native_like - 1),
            "Developing": (self.developing, self.proficient - 1),
            "Needs work": (self.needs_work, self.developing - 1),
        }
        return ranges.get(band, (0, 100))


# Level-specific thresholds
# Higher levels have stricter requirements
CEFR_THRESHOLDS = {
    "A1": LevelThresholds(
        native_like=85,
        proficient=70,
        developing=50,
        needs_work=0,
    ),
    "A2": LevelThresholds(
        native_like=88,
        proficient=72,
        developing=55,
        needs_work=0,
    ),
    "B1": LevelThresholds(
        native_like=90,
        proficient=75,
        developing=60,
        needs_work=0,
    ),
    "B2": LevelThresholds(
        native_like=92,
        proficient=78,
        developing=65,
        needs_work=0,
    ),
    "C1": LevelThresholds(
        native_like=94,
        proficient=82,
        developing=70,
        needs_work=0,
    ),
    "C2": LevelThresholds(
        native_like=96,
        proficient=85,
        developing=75,
        needs_work=0,
    ),
}


def get_thresholds(level: str) -> LevelThresholds:
    """Get thresholds for CEFR level."""
    return CEFR_THRESHOLDS.get(level, CEFR_THRESHOLDS["B1"])


def get_assessment_for_level(score: float, level: str) -> str:
    """
    Get level-appropriate assessment for score.

    Args:
        score: Fluency score (0-100)
        level: User's CEFR level

    Returns:
        Assessment string
    """
    thresholds = get_thresholds(level)
    return thresholds.get_band(score)


def get_progress_to_next_band(score: float, level: str) -> Dict:
    """
    Calculate progress to next assessment band.

    Args:
        score: Current fluency score
        level: User's CEFR level

    Returns:
        Dictionary with current band, next band, and progress percentage
    """
    thresholds = get_thresholds(level)
    current_band = thresholds.get_band(score)

    # Determine next band
    band_order = ["Needs work", "Developing", "Proficient", "Native-like"]
    current_idx = band_order.index(current_band)

    if current_idx == len(band_order) - 1:
        # Already at highest band
        return {
            "current_band": current_band,
            "next_band": None,
            "progress": 100,
            "points_needed": 0,
        }

    next_band = band_order[current_idx + 1]
    next_threshold = getattr(thresholds, next_band.lower().replace("-", "_").replace(" ", "_"))

    current_min, _ = thresholds.get_band_range(current_band)
    points_to_next = next_threshold - score
    band_width = next_threshold - current_min

    progress = ((score - current_min) / band_width * 100) if band_width > 0 else 0

    return {
        "current_band": current_band,
        "next_band": next_band,
        "progress": min(100, max(0, progress)),
        "points_needed": max(0, points_to_next),
    }


def suggest_target_level(score: float, current_level: str) -> str:
    """
    Suggest appropriate target CEFR level based on performance.

    Args:
        score: Fluency score
        current_level: User's current CEFR level

    Returns:
        Suggested target level
    """
    thresholds = get_thresholds(current_level)
    assessment = thresholds.get_band(score)

    level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
    current_idx = level_order.index(current_level) if current_level in level_order else 2

    if assessment == "Native-like" and score >= 95:
        # Consistently excellent - suggest moving up
        if current_idx < len(level_order) - 1:
            return level_order[current_idx + 1]
    elif assessment == "Needs work" and score < 40:
        # Struggling - suggest easier level
        if current_idx > 0:
            return level_order[current_idx - 1]

    return current_level
