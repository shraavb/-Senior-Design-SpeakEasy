"""
Bridge to existing Response Scorer.

Integrates with the dataset pipeline's response scoring system.
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import the existing response scorer
SCORER_AVAILABLE = False
try:
    import sys
    pipeline_path = Path(__file__).parent.parent.parent.parent
    if str(pipeline_path) not in sys.path:
        sys.path.insert(0, str(pipeline_path))

    from src.evaluation.response_scorer import ResponseScorer, EvaluationResult
    from src.evaluation.metrics import (
        calculate_vocabulary_score,
        calculate_slang_rate,
        calculate_bleu_score,
        calculate_semantic_similarity,
        determine_cefr_level,
    )
    SCORER_AVAILABLE = True
    logger.info("Response scorer available")
except ImportError as e:
    logger.warning(f"Response scorer not available: {e}")


class ResponseScorerBridge:
    """
    Bridge to the response scoring pipeline.

    Provides vocabulary, slang, BLEU, and semantic scoring.
    """

    def __init__(self):
        """Initialize the scorer bridge."""
        self.scorer = None

        if SCORER_AVAILABLE:
            try:
                self.scorer = ResponseScorer()
            except Exception as e:
                logger.warning(f"Failed to initialize ResponseScorer: {e}")

    def score(
        self,
        user_response: str,
        ground_truth: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Score a user response.

        Args:
            user_response: User's spoken text
            ground_truth: Expected text for comparison
            scenario: Conversation scenario

        Returns:
            Dictionary with vocabulary_score, slang_rate, bleu_score, etc.
        """
        if self.scorer is not None and ground_truth:
            try:
                result = self.scorer.score(
                    user_response=user_response,
                    ground_truth=ground_truth,
                    scenario=scenario or "general",
                )
                return {
                    "vocabulary_score": result.vocabulary_score,
                    "vocabulary_breakdown": result.vocabulary_breakdown,
                    "slang_rate": result.slang_rate,
                    "bleu_score": result.bleu_score,
                    "semantic_similarity": result.semantic_similarity,
                    "grammar_score": result.grammar_score,
                    "cefr_level": result.cefr_level,
                    "composite_score": result.composite_score,
                    "feedback": result.feedback,
                }
            except Exception as e:
                logger.error(f"Response scoring failed: {e}")

        # Fallback: simple scoring
        return self._simple_score(user_response, ground_truth)

    def _simple_score(
        self,
        user_response: str,
        ground_truth: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Simple fallback scoring without the full pipeline."""
        result = {
            "vocabulary_score": 0,
            "vocabulary_breakdown": {},
            "slang_rate": {"spanish": 0, "catalan": 0, "combined": 0},
            "bleu_score": 0.0,
            "semantic_similarity": 0.0,
            "grammar_score": 75.0,  # Assume reasonable
            "cefr_level": "B1",
            "composite_score": 0.5,
            "feedback": [],
        }

        if SCORER_AVAILABLE:
            try:
                # Use individual metric functions if available
                result["vocabulary_score"] = calculate_vocabulary_score(user_response)
                result["slang_rate"] = calculate_slang_rate(user_response)

                if ground_truth:
                    result["bleu_score"] = calculate_bleu_score(user_response, ground_truth)
                    result["semantic_similarity"] = calculate_semantic_similarity(
                        user_response, ground_truth
                    )

                result["cefr_level"] = determine_cefr_level(
                    result["vocabulary_score"],
                    result["grammar_score"]
                )
            except Exception as e:
                logger.warning(f"Fallback scoring partially failed: {e}")

        return result

    def calculate_vocabulary_score(self, text: str) -> Dict[str, Any]:
        """Calculate vocabulary score for text."""
        if SCORER_AVAILABLE:
            try:
                score = calculate_vocabulary_score(text)
                return {"score": score, "method": "full"}
            except Exception:
                pass

        # Simple fallback
        words = text.lower().split()
        unique_words = len(set(words))
        return {
            "score": min(15, unique_words // 2),
            "method": "fallback",
            "unique_words": unique_words,
        }

    def calculate_slang_rate(self, text: str) -> Dict[str, float]:
        """Calculate slang usage rates."""
        if SCORER_AVAILABLE:
            try:
                return calculate_slang_rate(text)
            except Exception:
                pass

        # Simple fallback
        from ..config import SPANISH_SLANG, CATALAN_EXPRESSIONS

        text_lower = text.lower()
        words = text_lower.split()
        total_words = len(words) if words else 1

        spanish_count = 0
        catalan_count = 0

        for slang_list in SPANISH_SLANG.values():
            for slang in slang_list:
                if slang in text_lower:
                    spanish_count += 1

        for expr_list in CATALAN_EXPRESSIONS.values():
            for expr in expr_list:
                if expr in text_lower:
                    catalan_count += 1

        return {
            "spanish": spanish_count / total_words,
            "catalan": catalan_count / total_words,
            "combined": (spanish_count + catalan_count) / total_words,
        }

    def calculate_similarity(
        self,
        hypothesis: str,
        reference: str,
    ) -> Dict[str, float]:
        """Calculate BLEU and semantic similarity."""
        result = {"bleu_score": 0.0, "semantic_similarity": 0.0}

        if SCORER_AVAILABLE:
            try:
                result["bleu_score"] = calculate_bleu_score(hypothesis, reference)
                result["semantic_similarity"] = calculate_semantic_similarity(
                    hypothesis, reference
                )
            except Exception as e:
                logger.warning(f"Similarity calculation failed: {e}")

        return result


# Singleton instance
_scorer_instance: Optional[ResponseScorerBridge] = None


def get_response_scorer() -> ResponseScorerBridge:
    """Get or create singleton response scorer."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = ResponseScorerBridge()
    return _scorer_instance
