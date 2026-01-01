"""
Pronunciation accuracy analyzer.

Evaluates phoneme accuracy, Catalan marker pronunciation, intonation, and stress.
"""

import re
from typing import Dict, Any, Optional, List
from .base import BaseAnalyzer
from ..config import CATALAN_EXPRESSIONS


class PronunciationAnalyzer(BaseAnalyzer):
    """
    Analyzes pronunciation accuracy.

    Metrics:
    - Phoneme-level accuracy (from ASR confidence)
    - Catalan marker pronunciation
    - Intonation contour matching
    - Stress placement
    """

    # Common Spanish pronunciation challenges
    CHALLENGING_SOUNDS = {
        "rr": ["perro", "carro", "correo", "tierra"],  # Rolled R
        "j": ["joven", "trabajo", "mejor"],            # Jota
        "ñ": ["año", "niño", "español"],              # Eñe
        "ll": ["calle", "lluvia", "ella"],            # Ll/Y distinction
        "z/c": ["zapato", "cielo", "cereza"],         # Theta (in Spain)
    }

    # Catalan-specific sounds
    CATALAN_SOUNDS = {
        "tx": ["txec", "cotxe"],                      # Catalan ch
        "ny": ["Catalunya", "anyell"],                 # Catalan ñ
        "l·l": ["intel·ligent", "col·legi"],          # Geminated L
    }

    def analyze(
        self,
        features: Any,
        transcript: Any,
        expected_text: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze pronunciation accuracy.

        Returns:
            Dictionary with:
            - score: Overall pronunciation accuracy (0-100)
            - phoneme_errors: List of detected errors
            - catalan_markers: Catalan expressions detected
            - catalan_marker_score: Pronunciation quality of Catalan
            - intonation_score: Intonation accuracy
            - stress_score: Word stress accuracy
        """
        text = transcript.text if hasattr(transcript, 'text') else str(transcript)
        words = transcript.words if hasattr(transcript, 'words') else []

        result = {
            "score": 75.0,
            "phoneme_errors": [],
            "catalan_markers": [],
            "catalan_marker_score": 0.0,
            "intonation_score": 75.0,
            "stress_score": 75.0,
            "confidence_based_score": 75.0,
        }

        # Calculate confidence-based pronunciation score
        if words:
            result["confidence_based_score"] = self._score_from_confidence(words)

        # Detect potential phoneme errors from low-confidence words
        result["phoneme_errors"] = self._detect_phoneme_errors(words, text)

        # Score Catalan marker pronunciation
        catalan_markers, catalan_score = self._score_catalan_markers(text, words, scenario)
        result["catalan_markers"] = catalan_markers
        result["catalan_marker_score"] = catalan_score

        # Score intonation (from pitch features)
        result["intonation_score"] = self._score_intonation(features, expected_text)

        # Score stress patterns
        result["stress_score"] = self._score_stress_patterns(words, text)

        # Calculate composite score
        result["score"] = self._calculate_composite_score(result)

        return result

    def _score_from_confidence(self, words: List[dict]) -> float:
        """Calculate pronunciation score from ASR word confidence."""
        if not words:
            return 75.0

        confidences = [w.get("confidence", 1.0) for w in words]
        avg_confidence = sum(confidences) / len(confidences)

        # Scale confidence to score (0.7 confidence = 70 score, 1.0 = 100)
        return min(100, avg_confidence * 100)

    def _detect_phoneme_errors(
        self,
        words: List[dict],
        text: str,
    ) -> List[Dict[str, str]]:
        """Detect potential pronunciation errors from low-confidence words."""
        errors = []

        for word_info in words:
            word = word_info.get("word", "")
            confidence = word_info.get("confidence", 1.0)

            # Low confidence might indicate pronunciation issues
            if confidence < 0.8:
                # Check if word contains challenging sounds
                error_type = self._identify_challenging_sound(word.lower())
                if error_type:
                    errors.append({
                        "word": word,
                        "type": error_type,
                        "confidence": confidence,
                        "suggestion": self._get_pronunciation_suggestion(error_type),
                    })

        return errors[:5]  # Limit to top 5 errors

    def _identify_challenging_sound(self, word: str) -> Optional[str]:
        """Identify if word contains challenging Spanish sounds."""
        for sound, examples in self.CHALLENGING_SOUNDS.items():
            if sound == "rr" and "rr" in word:
                return "rolled_r"
            elif sound == "j" and "j" in word:
                return "jota"
            elif sound == "ñ" and "ñ" in word:
                return "ene"
            elif sound == "ll" and "ll" in word:
                return "ll_sound"
            elif sound == "z/c" and re.search(r'[zc][ei]', word):
                return "theta"

        return None

    def _get_pronunciation_suggestion(self, error_type: str) -> str:
        """Get practice suggestion for error type."""
        suggestions = {
            "rolled_r": "Practice the rolled 'rr' with tongue trills",
            "jota": "The 'j' is a strong guttural sound from the throat",
            "ene": "The 'ñ' is like 'ny' in canyon",
            "ll_sound": "In Catalan Spanish, 'll' is often pronounced like 'y'",
            "theta": "In Castilian Spanish, 'z' and 'ce/ci' are pronounced like 'th'",
        }
        return suggestions.get(error_type, "Focus on clear articulation")

    def _score_catalan_markers(
        self,
        text: str,
        words: List[dict],
        scenario: Optional[str] = None,
    ) -> tuple[List[str], float]:
        """Score pronunciation of Catalan expressions."""
        text_lower = text.lower()
        found_markers = []
        marker_scores = []

        # Get expected markers for scenario
        expected = CATALAN_EXPRESSIONS.get(scenario, []) if scenario else []

        # Check all Catalan expressions
        all_markers = set()
        for markers in CATALAN_EXPRESSIONS.values():
            all_markers.update(markers)

        for marker in all_markers:
            pattern = r'\b' + re.escape(marker) + r'\b'
            if re.search(pattern, text_lower):
                found_markers.append(marker)

                # Find confidence for this marker
                marker_confidence = 1.0
                for word_info in words:
                    if marker in word_info.get("word", "").lower():
                        marker_confidence = word_info.get("confidence", 1.0)
                        break

                marker_scores.append(marker_confidence * 100)

        if not marker_scores:
            return found_markers, 0.0

        return found_markers, sum(marker_scores) / len(marker_scores)

    def _score_intonation(
        self,
        features: Any,
        expected_text: Optional[str] = None,
    ) -> float:
        """Score intonation patterns."""
        if not hasattr(features, 'pitch_values') or len(features.pitch_values) == 0:
            return 75.0  # Default without pitch data

        # Check for question intonation (rising at end)
        if expected_text and expected_text.strip().endswith("?"):
            # Check if pitch rises at the end
            pitch_values = features.pitch_values
            if len(pitch_values) > 10:
                start_avg = sum(pitch_values[:5]) / 5
                end_avg = sum(pitch_values[-5:]) / 5

                if end_avg > start_avg:
                    return 100.0  # Correct rising intonation
                else:
                    return 60.0  # Missing question intonation

        # For statements, check for falling intonation at end
        if expected_text and not expected_text.strip().endswith("?"):
            pitch_values = features.pitch_values
            if len(pitch_values) > 10:
                start_avg = sum(pitch_values[:5]) / 5
                end_avg = sum(pitch_values[-5:]) / 5

                if end_avg < start_avg:
                    return 100.0  # Correct falling intonation
                elif abs(end_avg - start_avg) < start_avg * 0.1:
                    return 80.0  # Flat is acceptable
                else:
                    return 70.0  # Rising for statement is less natural

        return 75.0

    def _score_stress_patterns(self, words: List[dict], text: str) -> float:
        """Score word stress patterns (simplified)."""
        # This would ideally use phoneme-level alignment
        # For now, use duration variation as proxy for stress

        if len(words) < 3:
            return 75.0

        # Calculate word duration variation
        durations = [
            w.get("end", 0) - w.get("start", 0)
            for w in words
            if w.get("end", 0) > w.get("start", 0)
        ]

        if not durations:
            return 75.0

        avg_duration = sum(durations) / len(durations)
        variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)

        # Some variation is good (indicates stress), too much is bad
        cv = (variance ** 0.5) / avg_duration if avg_duration > 0 else 0

        if 0.2 <= cv <= 0.5:
            return 100.0  # Good stress variation
        elif cv < 0.2:
            return 70.0  # Too uniform (robotic)
        else:
            return 60.0  # Too variable (choppy)

    def _calculate_composite_score(self, result: Dict[str, Any]) -> float:
        """Calculate composite pronunciation score."""
        weights = {
            "confidence_based_score": 0.40,
            "catalan_marker_score": 0.20,
            "intonation_score": 0.20,
            "stress_score": 0.20,
        }

        score = 0.0
        for metric, weight in weights.items():
            value = result.get(metric, 75.0)
            # Handle case where catalan_marker_score is 0 (no markers expected)
            if metric == "catalan_marker_score" and value == 0:
                value = 75.0  # Neutral if no Catalan expected
            score += value * weight

        return self._clamp_score(score)
