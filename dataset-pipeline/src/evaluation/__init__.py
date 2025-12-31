"""
User Response Evaluation Module for SpeakEasy.

This module provides tools for evaluating user responses against ground truth
dialogues, calculating vocabulary scores, slang usage, and CEFR levels.
"""

from .response_scorer import ResponseScorer
from .metrics import (
    calculate_vocabulary_score,
    calculate_slang_rate,
    calculate_bleu_score,
    calculate_semantic_similarity,
    determine_cefr_level,
)

__all__ = [
    "ResponseScorer",
    "calculate_vocabulary_score",
    "calculate_slang_rate",
    "calculate_bleu_score",
    "calculate_semantic_similarity",
    "determine_cefr_level",
]
