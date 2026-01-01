"""
Bridge to existing CEFR classifier.

Integrates with the dataset pipeline's CEFR classification system.
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import the existing CEFR classifier
CEFR_AVAILABLE = False
try:
    import sys
    # Add parent path to allow importing from dataset-pipeline
    pipeline_path = Path(__file__).parent.parent.parent.parent
    if str(pipeline_path) not in sys.path:
        sys.path.insert(0, str(pipeline_path))

    from src.cefr_classifier import CEFRPipeline, CEFRClassification, RuleBasedAnalyzer
    CEFR_AVAILABLE = True
    logger.info("CEFR classifier available")
except ImportError as e:
    logger.warning(f"CEFR classifier not available: {e}")


class CEFRBridge:
    """
    Bridge to the CEFR classification pipeline.

    Provides CEFR level assessment for transcribed text.
    """

    def __init__(self, use_llm: bool = False):
        """
        Initialize the CEFR bridge.

        Args:
            use_llm: Whether to use LLM-based classification (slower but more accurate)
        """
        self.pipeline = None
        self.rule_analyzer = None
        self.use_llm = use_llm

        if CEFR_AVAILABLE:
            try:
                self.pipeline = CEFRPipeline(use_llm=use_llm)
                self.rule_analyzer = RuleBasedAnalyzer()
            except Exception as e:
                logger.warning(f"Failed to initialize CEFR pipeline: {e}")

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify text for CEFR level.

        Args:
            text: Text to classify

        Returns:
            Dictionary with cefr_level, simplified_level, confidence, reasoning
        """
        if self.pipeline is not None:
            try:
                result = self.pipeline.classify(text)
                return {
                    "cefr_level": result.cefr_level,
                    "simplified_level": result.simplified_level,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                    "linguistic_features": result.linguistic_features,
                    "method": result.method,
                }
            except Exception as e:
                logger.error(f"CEFR classification failed: {e}")

        # Fallback: simple rule-based estimation
        return self._simple_classify(text)

    def _simple_classify(self, text: str) -> Dict[str, Any]:
        """Simple fallback classification without the full pipeline."""
        text_lower = text.lower()
        complexity_score = 0

        # Check for complexity indicators
        complexity_markers = {
            # Subjunctive indicators
            "hubiera": 3, "pudiera": 3, "quisiera": 3,
            "sea": 2, "este": 2, "tenga": 2,
            # Conditional
            "sería": 2, "estaría": 2, "tendría": 2,
            # Past tenses
            "había": 1, "era": 1, "estaba": 1,
            # Discourse complexity
            "sin embargo": 3, "no obstante": 3, "por lo tanto": 2,
            "aunque": 2, "porque": 1, "pero": 1,
        }

        for marker, score in complexity_markers.items():
            if marker in text_lower:
                complexity_score += score

        # Determine level based on score
        if complexity_score >= 6:
            level = "C1"
            simplified = "mastery"
        elif complexity_score >= 4:
            level = "B2"
            simplified = "advanced"
        elif complexity_score >= 2:
            level = "B1"
            simplified = "intermediate"
        elif complexity_score >= 1:
            level = "A2"
            simplified = "beginner"
        else:
            level = "A1"
            simplified = "beginner"

        return {
            "cefr_level": level,
            "simplified_level": simplified,
            "confidence": 0.6,  # Lower confidence for fallback
            "reasoning": f"Simple analysis based on {complexity_score} complexity markers",
            "linguistic_features": {"complexity_score": complexity_score},
            "method": "fallback",
        }

    def get_linguistic_features(self, text: str) -> Dict[str, Any]:
        """Extract linguistic features from text."""
        if self.rule_analyzer is not None:
            try:
                return self.rule_analyzer.analyze(text)
            except Exception as e:
                logger.error(f"Feature extraction failed: {e}")

        return {"error": "Feature extraction not available"}


def assess_cefr_level(
    transcript_text: str,
    fluency_score: float,
    user_claimed_level: str = "B1",
) -> str:
    """
    Assess CEFR level combining transcript analysis and fluency score.

    Args:
        transcript_text: Transcribed speech
        fluency_score: Overall fluency score (0-100)
        user_claimed_level: User's self-reported level

    Returns:
        Assessed CEFR level (A1-C2)
    """
    bridge = CEFRBridge(use_llm=False)  # Use rule-based for speed
    result = bridge.classify(transcript_text)

    text_level = result.get("cefr_level", user_claimed_level)

    # Combine text complexity with fluency performance
    level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]

    text_idx = level_order.index(text_level) if text_level in level_order else 2
    claimed_idx = level_order.index(user_claimed_level) if user_claimed_level in level_order else 2

    # Adjust based on fluency score
    if fluency_score >= 90:
        # Excellent performance - could be at or above claimed level
        final_idx = max(text_idx, claimed_idx)
    elif fluency_score >= 75:
        # Good performance - likely at claimed level
        final_idx = claimed_idx
    elif fluency_score >= 60:
        # Developing - average of text and claimed
        final_idx = (text_idx + claimed_idx) // 2
    else:
        # Struggling - might be below claimed level
        final_idx = min(text_idx, claimed_idx - 1) if claimed_idx > 0 else 0

    final_idx = max(0, min(len(level_order) - 1, final_idx))
    return level_order[final_idx]


# Singleton instance
_bridge_instance: Optional[CEFRBridge] = None


def get_cefr_bridge(use_llm: bool = False) -> CEFRBridge:
    """Get or create singleton CEFR bridge."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = CEFRBridge(use_llm=use_llm)
    return _bridge_instance
