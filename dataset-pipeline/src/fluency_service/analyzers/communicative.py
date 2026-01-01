"""
Communicative competence analyzer.

Evaluates register appropriateness, discourse markers, and turn-taking.
"""

import re
from typing import Dict, Any, Optional, List, Set
from .base import BaseAnalyzer
from ..config import DISCOURSE_MARKERS


class CommunicativeAnalyzer(BaseAnalyzer):
    """
    Analyzes communicative competence.

    Metrics:
    - Register appropriateness (formal vs. informal)
    - Discourse marker usage
    - Turn-taking patterns
    """

    # Formal indicators
    FORMAL_MARKERS = {
        "pronouns": ["usted", "ustedes"],
        "verbs": ["podría", "sería", "quisiera", "desearía"],
        "phrases": ["disculpe", "perdone", "con su permiso", "le agradezco"],
        "greetings": ["buenos días", "buenas tardes", "buenas noches"],
    }

    # Informal indicators
    INFORMAL_MARKERS = {
        "pronouns": ["tú", "vosotros"],
        "verbs": ["puedes", "quieres", "mola", "flipas"],
        "phrases": ["oye", "mira", "tío", "tía", "colega", "chaval"],
        "greetings": ["hola", "qué tal", "qué pasa", "hey"],
        "catalan": ["nen", "nena", "home", "ostres", "vinga"],
    }

    # Expected register by scenario
    SCENARIO_REGISTER = {
        "greetings": "flexible",      # Can be formal or informal
        "farewells": "flexible",
        "family": "informal",         # Family is typically informal
        "emotions": "informal",       # Emotional expression is informal
        "plans": "flexible",
        "requests": "polite",         # Requests should be polite (formal or polite informal)
    }

    def analyze(
        self,
        features: Any,
        transcript: Any,
        expected_text: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze communicative competence.

        Returns:
            Dictionary with:
            - score: Overall communicative competence (0-100)
            - register_match: Detected register (formal/informal/mixed)
            - register_appropriateness: 0-1 score
            - discourse_markers_used: List of markers found
            - discourse_markers_expected: Markers appropriate for context
            - turn_taking_score: Quality of turn-taking signals
        """
        text = transcript.text if hasattr(transcript, 'text') else str(transcript)
        text_lower = text.lower()
        words = transcript.words if hasattr(transcript, 'words') else []

        result = {
            "score": 75.0,
            "register_match": "neutral",
            "register_appropriateness": 0.75,
            "discourse_markers_used": [],
            "discourse_markers_expected": [],
            "turn_taking_score": 75.0,
        }

        # Detect register
        register, register_score = self._analyze_register(text_lower, scenario)
        result["register_match"] = register
        result["register_appropriateness"] = register_score / 100.0

        # Detect discourse markers
        markers_used = self._detect_discourse_markers(text_lower)
        result["discourse_markers_used"] = markers_used

        # Get expected markers for context
        result["discourse_markers_expected"] = self._get_expected_markers(scenario)

        # Score discourse marker usage
        discourse_score = self._score_discourse_markers(markers_used, scenario)

        # Score turn-taking
        turn_score = self._score_turn_taking(text_lower, words)
        result["turn_taking_score"] = turn_score

        # Calculate composite score
        result["score"] = self._calculate_composite_score(
            register_score, discourse_score, turn_score
        )

        return result

    def _analyze_register(
        self,
        text: str,
        scenario: Optional[str] = None,
    ) -> tuple[str, float]:
        """Analyze register and appropriateness."""
        formal_count = 0
        informal_count = 0

        # Count formal markers
        for category, markers in self.FORMAL_MARKERS.items():
            for marker in markers:
                if re.search(r'\b' + re.escape(marker) + r'\b', text, re.IGNORECASE):
                    formal_count += 1

        # Count informal markers
        for category, markers in self.INFORMAL_MARKERS.items():
            for marker in markers:
                if re.search(r'\b' + re.escape(marker) + r'\b', text, re.IGNORECASE):
                    informal_count += 1

        # Determine register
        if formal_count > informal_count * 2:
            register = "formal"
        elif informal_count > formal_count * 2:
            register = "informal"
        elif formal_count > 0 and informal_count > 0:
            register = "mixed"
        else:
            register = "neutral"

        # Check appropriateness for scenario
        expected = self.SCENARIO_REGISTER.get(scenario, "flexible")

        if expected == "flexible":
            score = 100.0  # Any register is fine
        elif expected == "polite":
            # Polite can be formal or respectful informal
            if register in ["formal", "neutral"]:
                score = 100.0
            elif register == "mixed":
                score = 80.0
            else:
                score = 60.0  # Too casual for requests
        elif expected == "informal":
            if register in ["informal", "neutral"]:
                score = 100.0
            elif register == "mixed":
                score = 85.0
            else:
                score = 70.0  # Too formal for family
        else:
            score = 80.0

        return register, score

    def _detect_discourse_markers(self, text: str) -> List[str]:
        """Detect discourse markers in text."""
        found = []

        for category, markers in DISCOURSE_MARKERS.items():
            for marker in markers:
                pattern = r'\b' + re.escape(marker) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    found.append(marker)

        return list(set(found))  # Remove duplicates

    def _get_expected_markers(self, scenario: Optional[str] = None) -> List[str]:
        """Get expected discourse markers for scenario."""
        # Common connectors are always appropriate
        base_markers = ["bueno", "pues", "entonces"]

        scenario_specific = {
            "greetings": ["mira", "oye"],
            "farewells": ["bueno", "pues"],
            "family": ["sabes", "mira"],
            "emotions": ["la verdad", "en serio"],
            "plans": ["así que", "entonces", "por eso"],
            "requests": ["mira", "escucha", "oye"],
        }

        specific = scenario_specific.get(scenario, [])
        return list(set(base_markers + specific))

    def _score_discourse_markers(
        self,
        markers_used: List[str],
        scenario: Optional[str] = None,
    ) -> float:
        """Score discourse marker usage."""
        if not markers_used:
            return 60.0  # Some markers expected in natural speech

        # More markers (up to a point) indicates fluency
        count = len(markers_used)

        if count == 1:
            return 70.0
        elif count == 2:
            return 85.0
        elif count >= 3:
            return 100.0

        return 60.0

    def _score_turn_taking(
        self,
        text: str,
        words: List[dict],
    ) -> float:
        """Score turn-taking signals."""
        score = 75.0

        # Check for turn-taking markers
        turn_markers = DISCOURSE_MARKERS.get("turn_taking", [])
        markers_found = 0

        for marker in turn_markers:
            if re.search(r'\b' + re.escape(marker) + r'\b', text, re.IGNORECASE):
                markers_found += 1

        if markers_found > 0:
            score += 10

        # Check response timing (if we have word timestamps)
        if words:
            first_word_start = words[0].get("start", 0)

            # Good response timing (not too fast, not too slow)
            if 0.2 <= first_word_start <= 1.0:
                score += 15
            elif first_word_start > 2.0:
                score -= 10  # Too slow

        return self._clamp_score(score)

    def _calculate_composite_score(
        self,
        register_score: float,
        discourse_score: float,
        turn_score: float,
    ) -> float:
        """Calculate composite communicative competence score."""
        return self._clamp_score(
            0.40 * register_score +
            0.35 * discourse_score +
            0.25 * turn_score
        )
