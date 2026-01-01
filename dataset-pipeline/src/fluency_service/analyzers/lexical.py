"""
Lexical accuracy analyzer.

Evaluates word accuracy (WER), Catalan expression usage, and phrase completeness.
"""

import re
from typing import Dict, Any, Optional, List, Set
from .base import BaseAnalyzer
from ..config import CATALAN_EXPRESSIONS, SPANISH_SLANG

# Try to import jiwer for WER calculation
try:
    from jiwer import wer as calculate_wer
    JIWER_AVAILABLE = True
except ImportError:
    JIWER_AVAILABLE = False


class LexicalAnalyzer(BaseAnalyzer):
    """
    Analyzes lexical accuracy and vocabulary usage.

    Metrics:
    - Word Error Rate (WER) vs expected text
    - Catalan expression usage
    - Phrase completeness
    - Vocabulary level assessment
    """

    def analyze(
        self,
        features: Any,
        transcript: Any,
        expected_text: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze lexical accuracy.

        Returns:
            Dictionary with:
            - score: Overall lexical accuracy (0-100)
            - wer: Word Error Rate (0-1)
            - catalan_expressions_used: List of Catalan expressions found
            - catalan_expressions_expected: Expected expressions for scenario
            - expected_phrases_hit: Count of expected phrases present
            - vocabulary_level: Assessed vocabulary level
        """
        text = transcript.text if hasattr(transcript, 'text') else str(transcript)
        text_lower = text.lower()

        result = {
            "score": 50.0,
            "wer": 0.0,
            "catalan_expressions_used": [],
            "catalan_expressions_expected": [],
            "spanish_slang_used": [],
            "expected_phrases_hit": 0,
            "expected_phrases_total": 0,
            "vocabulary_level": "intermediate",
        }

        # Calculate WER if expected text is provided
        if expected_text and JIWER_AVAILABLE:
            result["wer"] = self._calculate_wer(text, expected_text)
        elif expected_text:
            result["wer"] = self._simple_wer(text, expected_text)

        # Detect Catalan expressions
        catalan_used, expected = self._detect_catalan_expressions(text_lower, scenario)
        result["catalan_expressions_used"] = catalan_used
        result["catalan_expressions_expected"] = expected

        # Detect Spanish slang
        result["spanish_slang_used"] = self._detect_spanish_slang(text_lower)

        # Calculate phrase completeness
        if expected_text:
            hit, total = self._check_phrase_completeness(text_lower, expected_text.lower())
            result["expected_phrases_hit"] = hit
            result["expected_phrases_total"] = total

        # Assess vocabulary level
        result["vocabulary_level"] = self._assess_vocabulary_level(
            catalan_used, result["spanish_slang_used"], text_lower
        )

        # Calculate composite score
        result["score"] = self._calculate_score(result)

        return result

    def _calculate_wer(self, hypothesis: str, reference: str) -> float:
        """Calculate Word Error Rate using jiwer."""
        if not hypothesis or not reference:
            return 0.0

        try:
            error_rate = calculate_wer(reference.lower(), hypothesis.lower())
            return min(1.0, error_rate)  # Cap at 1.0
        except Exception:
            return self._simple_wer(hypothesis, reference)

    def _simple_wer(self, hypothesis: str, reference: str) -> float:
        """Simple WER calculation without external library."""
        hyp_words = hypothesis.lower().split()
        ref_words = reference.lower().split()

        if not ref_words:
            return 0.0

        # Simple Levenshtein distance
        m, n = len(hyp_words), len(ref_words)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if hyp_words[i-1] == ref_words[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

        return dp[m][n] / n

    def _detect_catalan_expressions(
        self, text: str, scenario: Optional[str] = None
    ) -> tuple[List[str], List[str]]:
        """Detect Catalan expressions in text."""
        found = []
        expected = []

        # Get expected expressions for scenario
        if scenario and scenario in CATALAN_EXPRESSIONS:
            expected = CATALAN_EXPRESSIONS[scenario]

        # Check all Catalan expressions
        all_expressions = set()
        for expressions in CATALAN_EXPRESSIONS.values():
            all_expressions.update(expressions)

        for expr in all_expressions:
            pattern = r'\b' + re.escape(expr) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found.append(expr)

        return found, expected

    def _detect_spanish_slang(self, text: str) -> List[str]:
        """Detect Spanish slang usage."""
        found = []

        all_slang = set()
        for slang_list in SPANISH_SLANG.values():
            all_slang.update(slang_list)

        for slang in all_slang:
            pattern = r'\b' + re.escape(slang) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found.append(slang)

        return found

    def _check_phrase_completeness(self, text: str, expected: str) -> tuple[int, int]:
        """Check how many expected key phrases are present."""
        # Extract key phrases (words of 4+ characters)
        expected_words = set(
            w for w in expected.split()
            if len(w) >= 4 and not w.isdigit()
        )

        text_words = set(text.split())

        if not expected_words:
            return 0, 0

        hit = len(expected_words.intersection(text_words))
        return hit, len(expected_words)

    def _assess_vocabulary_level(
        self,
        catalan_used: List[str],
        slang_used: List[str],
        text: str,
    ) -> str:
        """Assess vocabulary level based on expression usage."""
        # Count complexity indicators
        advanced_count = len(catalan_used) + len(slang_used)

        # Check for complex structures
        complex_patterns = [
            r'\bsubj\w*\b',          # Subjunctive indicators
            r'\bhubiera\b',          # Past subjunctive
            r'\bpudiera\b',
            r'\bquisiera\b',
        ]

        for pattern in complex_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                advanced_count += 1

        if advanced_count >= 3:
            return "advanced"
        elif advanced_count >= 1:
            return "intermediate"
        else:
            return "beginner"

    def _calculate_score(self, result: Dict[str, Any]) -> float:
        """Calculate composite lexical score."""
        score = 100.0

        # WER penalty (major factor)
        wer_penalty = result["wer"] * 50  # Max 50 point penalty
        score -= wer_penalty

        # Bonus for Catalan expressions (if expected)
        if result["catalan_expressions_expected"]:
            expected_count = len(result["catalan_expressions_expected"])
            used_count = len([
                e for e in result["catalan_expressions_used"]
                if e in result["catalan_expressions_expected"]
            ])
            if expected_count > 0:
                expression_bonus = (used_count / expected_count) * 15
                score += expression_bonus

        # Phrase completeness bonus
        if result["expected_phrases_total"] > 0:
            completeness = result["expected_phrases_hit"] / result["expected_phrases_total"]
            score += completeness * 10

        return self._clamp_score(score)
