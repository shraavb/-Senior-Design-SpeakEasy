"""
Disfluency detection analyzer.

Detects filled pauses, repetitions, self-corrections, and false starts.
"""

import re
from typing import Dict, Any, Optional, List
from .base import BaseAnalyzer
from ..config import FILLED_PAUSES


class DisfluencyAnalyzer(BaseAnalyzer):
    """
    Analyzes speech disfluencies.

    Metrics (lower is better):
    - Filled pauses ("um", "uh", "eh")
    - Repetitions (word/phrase restarts)
    - Self-corrections (mid-word/phrase corrections)
    - False starts (abandoned utterances)
    """

    # Combined filled pause patterns
    FILLED_PAUSE_PATTERNS = [
        r'\b(eh+|uh+|um+|ah+|mm+)\b',           # Basic fillers
        r'\b(este|esto|pues|bueno)\b',          # Spanish fillers
        r'\b(doncs|o sigui)\b',                 # Catalan fillers
        r'\b(eee+|aaa+|ooo+)\b',                # Extended vowels
    ]

    # Repetition patterns
    REPETITION_PATTERNS = [
        r'\b(\w+)\s+\1\b',                      # Word repetition: "the the"
        r'\b(\w+)\s+(\w+)\s+\1\s+\2\b',        # Phrase repetition
    ]

    # Self-correction patterns
    CORRECTION_PATTERNS = [
        r'\b(\w+)\s*[-–]\s*(\w+)\b',           # Word correction: "casa- cosa"
        r'\bno,?\s+(no\s+)?quiero\s+decir\b',  # "I mean" corrections
        r'\bo sea\b',                          # Catalan/Spanish correction marker
        r'\bdigo\b',                           # "I say" correction
    ]

    def analyze(
        self,
        features: Any,
        transcript: Any,
        expected_text: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze disfluencies in speech.

        Returns:
            Dictionary with:
            - score: Disfluency score (0-100, lower = more disfluencies)
            - filled_pauses: List of detected filled pauses
            - repetitions: Count of repetitions
            - self_corrections: Count of self-corrections
            - false_starts: Count of false starts
            - disfluency_rate: Disfluencies per minute
        """
        text = transcript.text if hasattr(transcript, 'text') else str(transcript)
        text_lower = text.lower()

        result = {
            "score": 100.0,
            "filled_pauses": [],
            "filled_pause_count": 0,
            "repetitions": 0,
            "self_corrections": 0,
            "false_starts": 0,
            "disfluency_rate": 0.0,
        }

        # Detect filled pauses
        filled_pauses = self._detect_filled_pauses(text_lower)
        result["filled_pauses"] = filled_pauses
        result["filled_pause_count"] = len(filled_pauses)

        # Detect repetitions
        result["repetitions"] = self._count_repetitions(text_lower)

        # Detect self-corrections
        result["self_corrections"] = self._count_corrections(text_lower)

        # Detect false starts (from word timestamps if available)
        if hasattr(transcript, 'words') and transcript.words:
            result["false_starts"] = self._detect_false_starts(transcript.words)

        # Calculate disfluency rate
        total_disfluencies = (
            result["filled_pause_count"] +
            result["repetitions"] +
            result["self_corrections"] +
            result["false_starts"]
        )

        duration_minutes = features.duration_seconds / 60.0 if features.duration_seconds > 0 else 1
        result["disfluency_rate"] = total_disfluencies / duration_minutes

        # Calculate score (fewer disfluencies = higher score)
        # Target: <3 disfluencies per minute for advanced speakers
        result["score"] = self._calculate_score(result["disfluency_rate"])

        return result

    def _detect_filled_pauses(self, text: str) -> List[str]:
        """Detect filled pauses in text."""
        pauses = []

        for pattern in self.FILLED_PAUSE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            pauses.extend(matches)

        # Also check known filled pause words
        words = text.split()
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in FILLED_PAUSES.get("spanish", []):
                if clean_word not in pauses:
                    pauses.append(clean_word)
            if clean_word in FILLED_PAUSES.get("catalan", []):
                if clean_word not in pauses:
                    pauses.append(clean_word)

        return pauses

    def _count_repetitions(self, text: str) -> int:
        """Count word and phrase repetitions."""
        count = 0
        for pattern in self.REPETITION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count += len(matches)
        return count

    def _count_corrections(self, text: str) -> int:
        """Count self-corrections."""
        count = 0
        for pattern in self.CORRECTION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count += len(matches)
        return count

    def _detect_false_starts(self, words: List[dict]) -> int:
        """
        Detect false starts from word timings.

        A false start is characterized by:
        - Very short word followed by a pause
        - Incomplete word (if we had phoneme data)
        """
        false_starts = 0

        for i, word in enumerate(words[:-1]):
            word_duration = word.get("end", 0) - word.get("start", 0)
            word_text = word.get("word", "")

            # Very short word (< 100ms) followed by pause (> 300ms)
            if word_duration < 0.1 and len(word_text) <= 2:
                next_word = words[i + 1]
                gap = next_word.get("start", 0) - word.get("end", 0)
                if gap > 0.3:
                    false_starts += 1

        return false_starts

    def _calculate_score(self, disfluency_rate: float) -> float:
        """
        Calculate disfluency score from rate.

        Score mapping:
        - 0-1 per min: 100 (excellent)
        - 1-3 per min: 90-100 (good)
        - 3-5 per min: 70-90 (acceptable)
        - 5-10 per min: 50-70 (needs work)
        - 10+ per min: 0-50 (significant issues)
        """
        if disfluency_rate <= 1:
            return 100.0
        elif disfluency_rate <= 3:
            return 100 - (disfluency_rate - 1) * 5  # 90-100
        elif disfluency_rate <= 5:
            return 90 - (disfluency_rate - 3) * 10  # 70-90
        elif disfluency_rate <= 10:
            return 70 - (disfluency_rate - 5) * 4  # 50-70
        else:
            return max(0, 50 - (disfluency_rate - 10) * 5)
