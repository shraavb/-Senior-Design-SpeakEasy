"""
Temporal metrics analyzer.

Evaluates speaking rate, pause patterns, and response latency.
"""

from typing import Dict, Any, Optional, List
from .base import BaseAnalyzer


class TemporalAnalyzer(BaseAnalyzer):
    """
    Analyzes temporal aspects of speech fluency.

    Metrics:
    - Speaking rate (words/syllables per minute)
    - Pause placement and duration
    - Response latency
    """

    # Target speaking rates for Spanish by CEFR level (WPM)
    TARGET_RATES = {
        "A1": (80, 120),
        "A2": (100, 140),
        "B1": (120, 160),
        "B2": (140, 180),
        "C1": (150, 190),
        "C2": (160, 200),
    }

    # Acceptable pause durations (ms)
    ACCEPTABLE_PAUSE_MS = {
        "short": (200, 500),     # Between clauses
        "medium": (500, 1000),   # Between sentences
        "long": (1000, 2000),    # Paragraph breaks
    }

    def analyze(
        self,
        features: Any,
        transcript: Any,
        expected_text: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze temporal characteristics of speech.

        Returns:
            Dictionary with:
            - score: Overall temporal fluency score (0-100)
            - speaking_rate_wpm: Words per minute
            - pause_analysis: Pause statistics
            - response_latency_ms: Time before first word
        """
        result = {
            "score": 50.0,
            "speaking_rate_wpm": 0.0,
            "target_rate_wpm": 150.0,
            "pause_analysis": {},
            "response_latency_ms": None,
            "total_speech_duration_ms": 0.0,
            "total_pause_duration_ms": 0.0,
        }

        # Calculate speaking rate
        if hasattr(transcript, 'words') and transcript.words:
            word_count = len(transcript.words)
            duration_minutes = features.duration_seconds / 60.0

            if duration_minutes > 0:
                result["speaking_rate_wpm"] = word_count / duration_minutes

            # Calculate response latency (time to first word)
            if transcript.words:
                first_word_start = transcript.words[0].get("start", 0) * 1000
                result["response_latency_ms"] = first_word_start

        # Analyze pauses
        if hasattr(features, 'pause_durations') and features.pause_durations:
            pause_analysis = self._analyze_pauses(features.pause_durations)
            result["pause_analysis"] = pause_analysis
            result["total_pause_duration_ms"] = sum(features.pause_durations)

        # Calculate speech duration
        result["total_speech_duration_ms"] = (
            features.duration_seconds * 1000 - result["total_pause_duration_ms"]
        )

        # Calculate component scores
        rate_score = self._score_speaking_rate(result["speaking_rate_wpm"])
        pause_score = self._score_pauses(result["pause_analysis"])
        latency_score = self._score_latency(result["response_latency_ms"])

        # Combine scores (weighted)
        result["score"] = self._clamp_score(
            0.5 * rate_score + 0.3 * pause_score + 0.2 * latency_score
        )

        return result

    def _analyze_pauses(self, pause_durations: List[float]) -> Dict[str, Any]:
        """Analyze pause patterns."""
        if not pause_durations:
            return {
                "count": 0,
                "avg_duration_ms": 0,
                "placement_score": 100,
            }

        short = sum(1 for p in pause_durations if 200 <= p < 500)
        medium = sum(1 for p in pause_durations if 500 <= p < 1000)
        long = sum(1 for p in pause_durations if 1000 <= p < 2000)
        very_long = sum(1 for p in pause_durations if p >= 2000)

        # Calculate placement score (penalize very long pauses)
        total_pauses = len(pause_durations)
        acceptable_ratio = (short + medium + long) / total_pauses if total_pauses > 0 else 1
        placement_score = acceptable_ratio * 100

        return {
            "count": total_pauses,
            "avg_duration_ms": sum(pause_durations) / total_pauses,
            "short_pauses": short,
            "medium_pauses": medium,
            "long_pauses": long,
            "very_long_pauses": very_long,
            "placement_score": placement_score,
        }

    def _score_speaking_rate(self, rate_wpm: float, level: str = "B1") -> float:
        """Score speaking rate against target range."""
        min_rate, max_rate = self.TARGET_RATES.get(level, (120, 160))

        if min_rate <= rate_wpm <= max_rate:
            return 100.0  # Perfect range

        if rate_wpm < min_rate:
            # Too slow
            deviation = (min_rate - rate_wpm) / min_rate
            return max(0, 100 - deviation * 100)
        else:
            # Too fast
            deviation = (rate_wpm - max_rate) / max_rate
            return max(0, 100 - deviation * 50)  # Less penalty for fast speech

    def _score_pauses(self, pause_analysis: Dict[str, Any]) -> float:
        """Score pause patterns."""
        if not pause_analysis or pause_analysis.get("count", 0) == 0:
            return 100.0

        # Start with placement score
        score = pause_analysis.get("placement_score", 100)

        # Penalize too many very long pauses
        very_long = pause_analysis.get("very_long_pauses", 0)
        if very_long > 0:
            score -= very_long * 10

        return max(0, score)

    def _score_latency(self, latency_ms: Optional[float]) -> float:
        """Score response latency."""
        if latency_ms is None:
            return 100.0

        # Ideal: 200-800ms
        if 200 <= latency_ms <= 800:
            return 100.0

        if latency_ms < 200:
            # Too quick (might indicate interruption)
            return 90.0

        # Too slow
        excess_ms = latency_ms - 800
        penalty = min(excess_ms / 1000 * 30, 50)  # Max 50 point penalty
        return max(50, 100 - penalty)
