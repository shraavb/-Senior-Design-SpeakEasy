"""
Prosodic quality analyzer.

Evaluates pitch range, emotional congruence, volume consistency, and rhythm.
"""

from typing import Dict, Any, Optional, List
import numpy as np
from .base import BaseAnalyzer


class ProsodicAnalyzer(BaseAnalyzer):
    """
    Analyzes prosodic aspects of speech.

    Metrics:
    - Pitch range and variation
    - Emotional congruence with context
    - Volume consistency
    - Rhythm naturalness (PVI)
    """

    # Expected pitch ranges by speaker type (Hz)
    PITCH_RANGES = {
        "male": (85, 180),
        "female": (165, 255),
        "default": (100, 250),
    }

    # Expected PVI ranges for Spanish (syllable-timed)
    # Lower PVI = more syllable-timed (typical for Spanish)
    PVI_SPANISH_RANGE = (30, 50)

    # Emotion-scenario mapping for congruence checking
    SCENARIO_EMOTIONS = {
        "greetings": ["neutral", "happy", "excited"],
        "farewells": ["neutral", "sad", "warm"],
        "family": ["warm", "nostalgic", "neutral"],
        "emotions": ["varied"],  # Any emotion appropriate
        "plans": ["neutral", "excited", "hopeful"],
        "requests": ["polite", "neutral"],
    }

    def analyze(
        self,
        features: Any,
        transcript: Any,
        expected_text: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze prosodic characteristics.

        Returns:
            Dictionary with:
            - score: Overall prosodic quality (0-100)
            - pitch_range_hz: [min, max] pitch
            - pitch_mean_hz: Mean pitch
            - emotional_congruence: 0-1 score
            - volume_consistency: 0-1 score
            - rhythm_score: Rhythm naturalness (0-100)
            - pvi: Pairwise Variability Index
        """
        result = {
            "score": 50.0,
            "pitch_range_hz": [0.0, 0.0],
            "pitch_mean_hz": 0.0,
            "pitch_std_hz": 0.0,
            "emotional_congruence": 0.5,
            "volume_consistency": 0.5,
            "rhythm_score": 50.0,
            "pvi": 0.0,
        }

        # Extract pitch metrics from features
        if hasattr(features, 'pitch_mean') and features.pitch_mean > 0:
            result["pitch_mean_hz"] = features.pitch_mean
            result["pitch_std_hz"] = features.pitch_std
            result["pitch_range_hz"] = [features.pitch_min, features.pitch_max]

        # Extract PVI
        if hasattr(features, 'pvi'):
            result["pvi"] = features.pvi

        # Calculate component scores
        pitch_score = self._score_pitch_variation(
            result["pitch_mean_hz"],
            result["pitch_std_hz"],
            result["pitch_range_hz"],
        )

        rhythm_score = self._score_rhythm(result["pvi"])
        result["rhythm_score"] = rhythm_score

        volume_score = self._score_volume_consistency(features)
        result["volume_consistency"] = volume_score / 100.0

        emotion_score = self._score_emotional_congruence(features, scenario)
        result["emotional_congruence"] = emotion_score / 100.0

        # Calculate composite score
        result["score"] = self._clamp_score(
            0.35 * pitch_score +
            0.25 * rhythm_score +
            0.20 * volume_score +
            0.20 * emotion_score
        )

        return result

    def _score_pitch_variation(
        self,
        mean: float,
        std: float,
        range_hz: List[float],
    ) -> float:
        """Score pitch characteristics."""
        if mean <= 0:
            return 50.0  # No pitch data

        # Check if pitch is in normal range
        min_expected, max_expected = self.PITCH_RANGES["default"]
        range_score = 100.0

        if mean < min_expected:
            range_score -= (min_expected - mean) / min_expected * 30
        elif mean > max_expected:
            range_score -= (mean - max_expected) / max_expected * 30

        # Check variation (too flat = monotone, too variable = erratic)
        # Ideal std is about 10-20% of mean
        ideal_std_ratio = 0.15
        actual_ratio = std / mean if mean > 0 else 0

        if actual_ratio < 0.05:
            # Too monotone
            variation_score = 60 + actual_ratio / 0.05 * 40
        elif actual_ratio > 0.30:
            # Too variable
            variation_score = 100 - (actual_ratio - 0.30) / 0.30 * 50
        else:
            variation_score = 100.0

        return self._clamp_score((range_score + variation_score) / 2)

    def _score_rhythm(self, pvi: float) -> float:
        """
        Score rhythm based on PVI.

        Spanish is syllable-timed with lower PVI (30-50).
        """
        if pvi <= 0:
            return 50.0  # No PVI data

        min_pvi, max_pvi = self.PVI_SPANISH_RANGE

        if min_pvi <= pvi <= max_pvi:
            return 100.0  # Perfect Spanish rhythm

        if pvi < min_pvi:
            # Too regular (machine-like)
            deviation = (min_pvi - pvi) / min_pvi
            return max(60, 100 - deviation * 40)
        else:
            # Too variable (stress-timed, less Spanish-like)
            deviation = (pvi - max_pvi) / max_pvi
            return max(50, 100 - deviation * 50)

    def _score_volume_consistency(self, features: Any) -> float:
        """Score volume/intensity consistency."""
        if not hasattr(features, 'intensity_std') or features.intensity_mean <= 0:
            return 75.0  # Default

        # Calculate coefficient of variation
        cv = features.intensity_std / features.intensity_mean

        # Ideal CV is 0.1-0.3 (some variation but not too much)
        if cv < 0.05:
            return 80.0  # Too consistent (robotic)
        elif cv < 0.10:
            return 90.0
        elif cv <= 0.30:
            return 100.0  # Ideal range
        elif cv <= 0.50:
            return 80.0  # Somewhat inconsistent
        else:
            return max(50, 100 - (cv - 0.50) * 100)

    def _score_emotional_congruence(
        self,
        features: Any,
        scenario: Optional[str] = None,
    ) -> float:
        """
        Score emotional appropriateness for context.

        Uses prosodic features as proxy for emotion:
        - High pitch variation + high speaking rate = excited/happy
        - Low pitch variation + slow rate = sad/calm
        - etc.
        """
        if not scenario:
            return 75.0  # Default without context

        expected_emotions = self.SCENARIO_EMOTIONS.get(scenario, ["neutral"])

        if "varied" in expected_emotions:
            return 85.0  # Emotions scenario allows any emotion

        # Simple emotion detection from prosody
        detected_emotion = self._detect_emotion_from_prosody(features)

        if detected_emotion in expected_emotions:
            return 100.0
        elif "neutral" in expected_emotions:
            return 80.0  # Neutral is usually acceptable
        else:
            return 60.0  # Mismatched emotion

    def _detect_emotion_from_prosody(self, features: Any) -> str:
        """Simple emotion detection from prosodic features."""
        if not hasattr(features, 'pitch_std') or features.pitch_mean <= 0:
            return "neutral"

        pitch_variation = features.pitch_std / features.pitch_mean if features.pitch_mean > 0 else 0
        speech_ratio = getattr(features, 'speech_ratio', 0.8)

        # Simple heuristics
        if pitch_variation > 0.25 and speech_ratio > 0.85:
            return "excited"
        elif pitch_variation < 0.08:
            return "sad"
        elif pitch_variation > 0.15:
            return "happy"
        else:
            return "neutral"
