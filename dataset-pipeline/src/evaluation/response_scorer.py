#!/usr/bin/env python3
"""
Response Scorer for User Evaluation.

This module provides the main ResponseScorer class for evaluating user responses
against ground truth dialogues in the SpeakEasy language learning platform.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict

from .metrics import (
    calculate_vocabulary_score,
    calculate_slang_rate,
    calculate_bleu_score,
    calculate_semantic_similarity,
    determine_cefr_level,
    calculate_composite_score,
    generate_feedback,
)


@dataclass
class EvaluationResult:
    """Container for evaluation results."""
    id: str
    scenario: str
    user_response: str
    ground_truth: str

    # Scores
    vocabulary_score: int
    vocabulary_breakdown: Dict
    slang_rate: Dict
    bleu_score: float
    semantic_similarity: float
    grammar_score: float
    cefr_level: str
    composite_score: float

    # Feedback
    feedback: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ResponseScorer:
    """
    Main class for scoring user responses against ground truth.

    Usage:
        scorer = ResponseScorer()
        result = scorer.score(
            user_response="¡Hola, nen! ¿Qué tal?",
            ground_truth="¡Hola! ¿Qué tal, nen?",
            scenario="greetings"
        )
        print(result.composite_score)
        print(result.feedback)
    """

    def __init__(
        self,
        vocabulary_file: Optional[str] = None,
        rubrics_file: Optional[str] = None,
    ):
        """
        Initialize the scorer.

        Args:
            vocabulary_file: Path to scenario_vocabulary.json
            rubrics_file: Path to user_assessment_rubrics.json
        """
        self.vocabulary = {}
        self.rubrics = {}

        # Load vocabulary definitions
        if vocabulary_file:
            self._load_vocabulary(vocabulary_file)
        else:
            # Try default location
            default_vocab = Path(__file__).parent.parent.parent / "data/eval/scenario_vocabulary.json"
            if default_vocab.exists():
                self._load_vocabulary(str(default_vocab))

        # Load assessment rubrics
        if rubrics_file:
            self._load_rubrics(rubrics_file)
        else:
            default_rubrics = Path(__file__).parent.parent.parent / "data/eval/user_assessment_rubrics.json"
            if default_rubrics.exists():
                self._load_rubrics(str(default_rubrics))

    def _load_vocabulary(self, filepath: str) -> None:
        """Load vocabulary definitions from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.vocabulary = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load vocabulary file: {e}")

    def _load_rubrics(self, filepath: str) -> None:
        """Load assessment rubrics from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.rubrics = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load rubrics file: {e}")

    def get_scenario_vocabulary(self, scenario: str) -> Dict:
        """Get vocabulary definitions for a specific scenario."""
        return self.vocabulary.get(scenario, {})

    def score(
        self,
        user_response: str,
        ground_truth: str,
        scenario: str = "general",
        response_id: str = "",
        include_grammar: bool = False,
    ) -> EvaluationResult:
        """
        Score a single user response.

        Args:
            user_response: The user's text response
            ground_truth: The reference/expected response
            scenario: Conversation scenario type
            response_id: Optional identifier for the response
            include_grammar: Whether to run grammar checking (slower)

        Returns:
            EvaluationResult with all scores and feedback
        """
        # Get scenario-specific vocabulary
        scenario_vocab = self.get_scenario_vocabulary(scenario)

        # Calculate all metrics
        vocab_result = calculate_vocabulary_score(user_response, scenario_vocab)
        slang_result = calculate_slang_rate(user_response)
        bleu = calculate_bleu_score(user_response, ground_truth)
        semantic = calculate_semantic_similarity(user_response, ground_truth)

        # Grammar score (placeholder - could integrate SpaCy)
        grammar = 100.0 if not include_grammar else self._check_grammar(user_response)

        # Determine CEFR level
        cefr = determine_cefr_level(vocab_result["total_score"], grammar)

        # Calculate composite score
        metrics = {
            "vocabulary_score": vocab_result["total_score"],
            "slang_rate": slang_result["combined_rate"],
            "bleu_score": bleu,
            "semantic_similarity": semantic,
            "grammar_score": grammar,
        }
        composite = calculate_composite_score(metrics)

        # Generate feedback
        feedback_metrics = {
            "vocabulary_score": vocab_result["total_score"],
            "vocabulary_breakdown": vocab_result,
            "slang_rate": slang_result,
            "semantic_similarity": semantic,
            "cefr_level": cefr,
        }
        feedback = generate_feedback(feedback_metrics, scenario)

        return EvaluationResult(
            id=response_id,
            scenario=scenario,
            user_response=user_response,
            ground_truth=ground_truth,
            vocabulary_score=vocab_result["total_score"],
            vocabulary_breakdown=vocab_result,
            slang_rate=slang_result,
            bleu_score=bleu,
            semantic_similarity=semantic,
            grammar_score=grammar,
            cefr_level=cefr,
            composite_score=composite,
            feedback=feedback,
        )

    def _check_grammar(self, text: str) -> float:
        """
        Check grammar using SpaCy (if available).

        Returns:
            Grammar score (0-100)
        """
        try:
            import spacy
            nlp = spacy.load("es_core_news_sm")
            doc = nlp(text)

            # Basic grammar checks
            issues = 0
            checks = 0

            # Check sentence structure
            for sent in doc.sents:
                checks += 1
                has_verb = any(token.pos_ == "VERB" for token in sent)
                if not has_verb:
                    issues += 1

            # Check for common errors (simplified)
            for token in doc:
                checks += 1
                # Check gender agreement (basic)
                if token.pos_ == "DET" and token.head.pos_ == "NOUN":
                    # This is a simplified check
                    pass

            if checks == 0:
                return 100.0
            return max(0, 100 - (issues / checks * 100))

        except Exception:
            # SpaCy not available or error
            return 100.0

    def score_batch(
        self,
        responses: List[Dict],
        progress_callback=None,
    ) -> List[EvaluationResult]:
        """
        Score a batch of responses.

        Args:
            responses: List of dicts with keys:
                - user_response: str
                - ground_truth: str
                - scenario: str (optional)
                - id: str (optional)
            progress_callback: Optional callback(current, total)

        Returns:
            List of EvaluationResult objects
        """
        results = []
        total = len(responses)

        for i, item in enumerate(responses):
            result = self.score(
                user_response=item.get("user_response", ""),
                ground_truth=item.get("ground_truth", ""),
                scenario=item.get("scenario", "general"),
                response_id=item.get("id", f"response_{i}"),
            )
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, total)

        return results

    def evaluate_against_ground_truth(
        self,
        user_responses: List[Dict],
        ground_truth_file: str,
    ) -> List[EvaluationResult]:
        """
        Evaluate user responses against a ground truth file.

        Args:
            user_responses: List of dicts with 'id' and 'response' keys
            ground_truth_file: Path to ground truth JSON file

        Returns:
            List of EvaluationResult objects
        """
        # Load ground truth
        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            ground_truth_data = json.load(f)

        # Create lookup by ID
        gt_lookup = {item["id"]: item for item in ground_truth_data}

        results = []
        for user_item in user_responses:
            response_id = user_item.get("id", "")
            user_response = user_item.get("response", "")

            if response_id in gt_lookup:
                gt_item = gt_lookup[response_id]
                result = self.score(
                    user_response=user_response,
                    ground_truth=gt_item.get("ground_truth", ""),
                    scenario=gt_item.get("scenario", "general"),
                    response_id=response_id,
                )
                results.append(result)

        return results

    def export_results(
        self,
        results: List[EvaluationResult],
        output_file: str,
        format: str = "json",
    ) -> None:
        """
        Export evaluation results to file.

        Args:
            results: List of EvaluationResult objects
            output_file: Output file path
            format: "json" or "csv"
        """
        if format == "json":
            data = [r.to_dict() for r in results]
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        elif format == "csv":
            import csv
            if not results:
                return

            fieldnames = [
                "id", "scenario", "vocabulary_score", "bleu_score",
                "semantic_similarity", "grammar_score", "cefr_level",
                "composite_score",
            ]

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in results:
                    row = {k: getattr(r, k) for k in fieldnames}
                    writer.writerow(row)

    def get_aggregate_stats(self, results: List[EvaluationResult]) -> Dict:
        """
        Calculate aggregate statistics from batch results.

        Args:
            results: List of EvaluationResult objects

        Returns:
            Dict with aggregate statistics
        """
        if not results:
            return {}

        vocab_scores = [r.vocabulary_score for r in results]
        bleu_scores = [r.bleu_score for r in results]
        semantic_scores = [r.semantic_similarity for r in results]
        composite_scores = [r.composite_score for r in results]

        cefr_counts = {}
        for r in results:
            cefr_counts[r.cefr_level] = cefr_counts.get(r.cefr_level, 0) + 1

        return {
            "total_responses": len(results),
            "vocabulary": {
                "mean": sum(vocab_scores) / len(vocab_scores),
                "min": min(vocab_scores),
                "max": max(vocab_scores),
            },
            "bleu": {
                "mean": sum(bleu_scores) / len(bleu_scores),
                "min": min(bleu_scores),
                "max": max(bleu_scores),
            },
            "semantic_similarity": {
                "mean": sum(semantic_scores) / len(semantic_scores),
                "min": min(semantic_scores),
                "max": max(semantic_scores),
            },
            "composite": {
                "mean": sum(composite_scores) / len(composite_scores),
                "min": min(composite_scores),
                "max": max(composite_scores),
            },
            "cefr_distribution": cefr_counts,
        }


def main():
    """Test the ResponseScorer."""
    print("Testing ResponseScorer...")

    scorer = ResponseScorer()

    # Test single response
    result = scorer.score(
        user_response="¡Hola, nen! ¿Qué tal? Mola mucho verte por aquí.",
        ground_truth="¡Hola! ¿Qué tal, nen? ¿Cómo va todo?",
        scenario="greetings",
        response_id="test_001",
    )

    print(f"\nUser response: {result.user_response}")
    print(f"Ground truth: {result.ground_truth}")
    print(f"\nScores:")
    print(f"  Vocabulary: {result.vocabulary_score}")
    print(f"  BLEU: {result.bleu_score:.3f}")
    print(f"  Semantic similarity: {result.semantic_similarity:.3f}")
    print(f"  Grammar: {result.grammar_score}")
    print(f"  CEFR Level: {result.cefr_level}")
    print(f"  Composite: {result.composite_score:.3f}")
    print(f"\nFeedback:")
    for fb in result.feedback:
        print(f"  - {fb}")

    # Test batch
    print("\n" + "="*50)
    print("Testing batch scoring...")

    test_batch = [
        {
            "id": "test_001",
            "user_response": "Hola. ¿Cómo está usted?",
            "ground_truth": "¡Hola, nen! ¿Qué tal?",
            "scenario": "greetings",
        },
        {
            "id": "test_002",
            "user_response": "¡Ei, tio! Què tal? Fa temps que no et veig!",
            "ground_truth": "¡Hola! ¿Qué tal? ¿Cómo va todo?",
            "scenario": "greetings",
        },
        {
            "id": "test_003",
            "user_response": "Vinga, apa! Ens veiem demà!",
            "ground_truth": "Vale, adiós. Hasta mañana.",
            "scenario": "farewells",
        },
    ]

    results = scorer.score_batch(test_batch)
    stats = scorer.get_aggregate_stats(results)

    print(f"\nAggregate Stats:")
    print(f"  Total responses: {stats['total_responses']}")
    print(f"  Mean vocabulary score: {stats['vocabulary']['mean']:.2f}")
    print(f"  Mean composite score: {stats['composite']['mean']:.3f}")
    print(f"  CEFR distribution: {stats['cefr_distribution']}")


if __name__ == "__main__":
    main()
