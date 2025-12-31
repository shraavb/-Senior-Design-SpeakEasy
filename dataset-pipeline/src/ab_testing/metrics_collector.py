#!/usr/bin/env python3
"""
Metrics Collector for A/B Testing.

This module collects and aggregates metrics for experiment analysis.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
import statistics


@dataclass
class UserMetrics:
    """Metrics collected for a single user session."""
    user_id: str
    experiment_id: str
    group: str
    session_id: str
    timestamp: str

    # Learning metrics
    vocabulary_scores: List[int] = field(default_factory=list)
    slang_usage_rates: List[float] = field(default_factory=list)
    bleu_scores: List[float] = field(default_factory=list)
    semantic_similarities: List[float] = field(default_factory=list)
    grammar_scores: List[float] = field(default_factory=list)
    cefr_levels: List[str] = field(default_factory=list)
    composite_scores: List[float] = field(default_factory=list)

    # Engagement metrics
    time_per_dialogue_seconds: List[float] = field(default_factory=list)
    dialogues_completed: int = 0
    dialogues_started: int = 0
    session_duration_seconds: float = 0

    # Self-reported metrics
    pre_confidence: Optional[int] = None  # 1-10 scale
    post_confidence: Optional[int] = None  # 1-10 scale
    nps_score: Optional[int] = None  # -100 to 100

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExperimentMetrics:
    """Aggregated metrics for an experiment group."""
    experiment_id: str
    group: str
    user_count: int

    # Aggregated learning metrics
    avg_vocabulary_score: float = 0
    avg_slang_usage_rate: float = 0
    avg_bleu_score: float = 0
    avg_semantic_similarity: float = 0
    avg_grammar_score: float = 0
    avg_composite_score: float = 0

    # CEFR distribution
    cefr_distribution: Dict[str, int] = field(default_factory=dict)

    # Engagement metrics
    avg_time_per_dialogue: float = 0
    completion_rate: float = 0
    avg_session_duration: float = 0

    # Self-reported metrics
    avg_confidence_improvement: float = 0
    avg_nps_score: float = 0

    def to_dict(self) -> Dict:
        return asdict(self)


class MetricsCollector:
    """
    Collects and manages metrics for A/B testing experiments.

    Usage:
        collector = MetricsCollector()

        # Record user metrics
        collector.record_response_metrics(
            user_id="user_001",
            experiment_id="pilot_v1",
            group="A",
            metrics={
                "vocabulary_score": 8,
                "slang_usage_rate": 0.15,
                "bleu_score": 0.72,
            }
        )

        # Get experiment summary
        summary = collector.get_experiment_summary("pilot_v1")
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize metrics collector.

        Args:
            storage_path: Directory for storing metrics data
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = (
                Path(__file__).parent.parent.parent /
                "data" / "experiments" / "metrics"
            )

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.user_metrics: Dict[str, UserMetrics] = {}
        self._load_metrics()

    def _get_user_key(self, user_id: str, experiment_id: str) -> str:
        """Generate unique key for user-experiment pair."""
        return f"{user_id}:{experiment_id}"

    def _load_metrics(self) -> None:
        """Load metrics from storage."""
        metrics_file = self.storage_path / "user_metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, record in data.items():
                        self.user_metrics[key] = UserMetrics(**record)
            except Exception as e:
                print(f"Warning: Could not load metrics: {e}")

    def _save_metrics(self) -> None:
        """Save metrics to storage."""
        metrics_file = self.storage_path / "user_metrics.json"
        data = {key: record.to_dict() for key, record in self.user_metrics.items()}
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_or_create_user_metrics(
        self,
        user_id: str,
        experiment_id: str,
        group: str,
        session_id: Optional[str] = None,
    ) -> UserMetrics:
        """
        Get existing user metrics or create new record.

        Args:
            user_id: User identifier
            experiment_id: Experiment ID
            group: "A" or "B"
            session_id: Optional session identifier

        Returns:
            UserMetrics record
        """
        key = self._get_user_key(user_id, experiment_id)

        if key not in self.user_metrics:
            self.user_metrics[key] = UserMetrics(
                user_id=user_id,
                experiment_id=experiment_id,
                group=group,
                session_id=session_id or f"session_{datetime.now().timestamp()}",
                timestamp=datetime.now().isoformat(),
            )

        return self.user_metrics[key]

    def record_response_metrics(
        self,
        user_id: str,
        experiment_id: str,
        group: str,
        metrics: Dict[str, Any],
    ) -> None:
        """
        Record metrics for a single response.

        Args:
            user_id: User identifier
            experiment_id: Experiment ID
            group: "A" or "B"
            metrics: Dict with metric values (vocabulary_score, slang_usage_rate, etc.)
        """
        user_metrics = self.get_or_create_user_metrics(user_id, experiment_id, group)

        # Append to lists
        if "vocabulary_score" in metrics:
            user_metrics.vocabulary_scores.append(metrics["vocabulary_score"])
        if "slang_usage_rate" in metrics:
            user_metrics.slang_usage_rates.append(metrics["slang_usage_rate"])
        if "bleu_score" in metrics:
            user_metrics.bleu_scores.append(metrics["bleu_score"])
        if "semantic_similarity" in metrics:
            user_metrics.semantic_similarities.append(metrics["semantic_similarity"])
        if "grammar_score" in metrics:
            user_metrics.grammar_scores.append(metrics["grammar_score"])
        if "cefr_level" in metrics:
            user_metrics.cefr_levels.append(metrics["cefr_level"])
        if "composite_score" in metrics:
            user_metrics.composite_scores.append(metrics["composite_score"])
        if "time_seconds" in metrics:
            user_metrics.time_per_dialogue_seconds.append(metrics["time_seconds"])

        user_metrics.dialogues_completed += 1
        self._save_metrics()

    def record_engagement_metrics(
        self,
        user_id: str,
        experiment_id: str,
        group: str,
        dialogues_started: int,
        dialogues_completed: int,
        session_duration_seconds: float,
    ) -> None:
        """
        Record engagement metrics for a session.

        Args:
            user_id: User identifier
            experiment_id: Experiment ID
            group: "A" or "B"
            dialogues_started: Number of dialogues started
            dialogues_completed: Number of dialogues completed
            session_duration_seconds: Total session time
        """
        user_metrics = self.get_or_create_user_metrics(user_id, experiment_id, group)
        user_metrics.dialogues_started = dialogues_started
        user_metrics.dialogues_completed = dialogues_completed
        user_metrics.session_duration_seconds = session_duration_seconds
        self._save_metrics()

    def record_self_reported_metrics(
        self,
        user_id: str,
        experiment_id: str,
        group: str,
        pre_confidence: Optional[int] = None,
        post_confidence: Optional[int] = None,
        nps_score: Optional[int] = None,
    ) -> None:
        """
        Record self-reported metrics from surveys.

        Args:
            user_id: User identifier
            experiment_id: Experiment ID
            group: "A" or "B"
            pre_confidence: Pre-test confidence (1-10)
            post_confidence: Post-test confidence (1-10)
            nps_score: Net Promoter Score (-100 to 100)
        """
        user_metrics = self.get_or_create_user_metrics(user_id, experiment_id, group)
        if pre_confidence is not None:
            user_metrics.pre_confidence = pre_confidence
        if post_confidence is not None:
            user_metrics.post_confidence = post_confidence
        if nps_score is not None:
            user_metrics.nps_score = nps_score
        self._save_metrics()

    def get_group_metrics(
        self,
        experiment_id: str,
        group: str
    ) -> ExperimentMetrics:
        """
        Calculate aggregated metrics for an experiment group.

        Args:
            experiment_id: Experiment ID
            group: "A" or "B"

        Returns:
            ExperimentMetrics with aggregated values
        """
        # Get all users in this group
        group_users = [
            m for m in self.user_metrics.values()
            if m.experiment_id == experiment_id and m.group == group
        ]

        if not group_users:
            return ExperimentMetrics(
                experiment_id=experiment_id,
                group=group,
                user_count=0,
            )

        # Aggregate metrics
        all_vocab = [s for u in group_users for s in u.vocabulary_scores]
        all_slang = [s for u in group_users for s in u.slang_usage_rates]
        all_bleu = [s for u in group_users for s in u.bleu_scores]
        all_semantic = [s for u in group_users for s in u.semantic_similarities]
        all_grammar = [s for u in group_users for s in u.grammar_scores]
        all_composite = [s for u in group_users for s in u.composite_scores]
        all_times = [t for u in group_users for t in u.time_per_dialogue_seconds]
        all_cefr = [c for u in group_users for c in u.cefr_levels]

        # Calculate CEFR distribution
        cefr_dist = {}
        for level in all_cefr:
            cefr_dist[level] = cefr_dist.get(level, 0) + 1

        # Completion rate
        total_started = sum(u.dialogues_started for u in group_users)
        total_completed = sum(u.dialogues_completed for u in group_users)
        completion_rate = total_completed / total_started if total_started > 0 else 0

        # Confidence improvement
        confidence_improvements = []
        for u in group_users:
            if u.pre_confidence is not None and u.post_confidence is not None:
                confidence_improvements.append(u.post_confidence - u.pre_confidence)

        # NPS scores
        nps_scores = [u.nps_score for u in group_users if u.nps_score is not None]

        return ExperimentMetrics(
            experiment_id=experiment_id,
            group=group,
            user_count=len(group_users),
            avg_vocabulary_score=statistics.mean(all_vocab) if all_vocab else 0,
            avg_slang_usage_rate=statistics.mean(all_slang) if all_slang else 0,
            avg_bleu_score=statistics.mean(all_bleu) if all_bleu else 0,
            avg_semantic_similarity=statistics.mean(all_semantic) if all_semantic else 0,
            avg_grammar_score=statistics.mean(all_grammar) if all_grammar else 0,
            avg_composite_score=statistics.mean(all_composite) if all_composite else 0,
            cefr_distribution=cefr_dist,
            avg_time_per_dialogue=statistics.mean(all_times) if all_times else 0,
            completion_rate=completion_rate,
            avg_session_duration=statistics.mean([u.session_duration_seconds for u in group_users]),
            avg_confidence_improvement=statistics.mean(confidence_improvements) if confidence_improvements else 0,
            avg_nps_score=statistics.mean(nps_scores) if nps_scores else 0,
        )

    def get_experiment_summary(self, experiment_id: str) -> Dict:
        """
        Get complete summary for an experiment comparing both groups.

        Args:
            experiment_id: Experiment ID

        Returns:
            Dict with comparison of Group A vs Group B
        """
        group_a = self.get_group_metrics(experiment_id, "A")
        group_b = self.get_group_metrics(experiment_id, "B")

        def calc_diff(a_val: float, b_val: float) -> Dict:
            """Calculate difference and percent change."""
            diff = b_val - a_val
            pct = (diff / a_val * 100) if a_val != 0 else 0
            return {"diff": diff, "pct_change": pct}

        return {
            "experiment_id": experiment_id,
            "group_a": group_a.to_dict(),
            "group_b": group_b.to_dict(),
            "comparison": {
                "vocabulary_score": calc_diff(group_a.avg_vocabulary_score, group_b.avg_vocabulary_score),
                "slang_usage_rate": calc_diff(group_a.avg_slang_usage_rate, group_b.avg_slang_usage_rate),
                "bleu_score": calc_diff(group_a.avg_bleu_score, group_b.avg_bleu_score),
                "composite_score": calc_diff(group_a.avg_composite_score, group_b.avg_composite_score),
                "completion_rate": calc_diff(group_a.completion_rate, group_b.completion_rate),
                "confidence_improvement": calc_diff(group_a.avg_confidence_improvement, group_b.avg_confidence_improvement),
            },
            "recommendation": self._generate_recommendation(group_a, group_b),
        }

    def _generate_recommendation(
        self,
        group_a: ExperimentMetrics,
        group_b: ExperimentMetrics
    ) -> str:
        """Generate recommendation based on metrics comparison."""
        if group_a.user_count < 5 or group_b.user_count < 5:
            return "Insufficient data for recommendation. Need at least 5 users per group."

        # Count wins
        a_wins = 0
        b_wins = 0

        if group_a.avg_composite_score > group_b.avg_composite_score:
            a_wins += 1
        else:
            b_wins += 1

        if group_a.avg_slang_usage_rate > group_b.avg_slang_usage_rate:
            a_wins += 1
        else:
            b_wins += 1

        if group_a.completion_rate > group_b.completion_rate:
            a_wins += 1
        else:
            b_wins += 1

        if group_a.avg_confidence_improvement > group_b.avg_confidence_improvement:
            a_wins += 1
        else:
            b_wins += 1

        if a_wins > b_wins:
            return f"Approach A appears superior ({a_wins}/{a_wins+b_wins} metrics). Consider broader rollout."
        elif b_wins > a_wins:
            return f"Approach B appears superior ({b_wins}/{a_wins+b_wins} metrics). Consider broader rollout."
        else:
            return "Results are inconclusive. Consider extending the experiment or investigating specific metrics."

    def export_summary(self, experiment_id: str, output_path: str) -> None:
        """Export experiment summary to JSON file."""
        summary = self.get_experiment_summary(experiment_id)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)


def main():
    """Test metrics collector."""
    print("Testing MetricsCollector")
    print("=" * 50)

    collector = MetricsCollector()

    # Simulate some test data
    test_data = [
        ("user_001", "A", {"vocabulary_score": 8, "slang_usage_rate": 0.15, "bleu_score": 0.72, "cefr_level": "B1"}),
        ("user_002", "A", {"vocabulary_score": 6, "slang_usage_rate": 0.10, "bleu_score": 0.65, "cefr_level": "A2"}),
        ("user_003", "B", {"vocabulary_score": 10, "slang_usage_rate": 0.22, "bleu_score": 0.78, "cefr_level": "B1"}),
        ("user_004", "B", {"vocabulary_score": 9, "slang_usage_rate": 0.18, "bleu_score": 0.75, "cefr_level": "B1"}),
        ("user_005", "A", {"vocabulary_score": 7, "slang_usage_rate": 0.12, "bleu_score": 0.68, "cefr_level": "B1"}),
    ]

    for user_id, group, metrics in test_data:
        collector.record_response_metrics(
            user_id=user_id,
            experiment_id="pilot_v1",
            group=group,
            metrics=metrics,
        )
        print(f"Recorded: {user_id} -> Group {group}")

    # Get summary
    print("\n" + "=" * 50)
    summary = collector.get_experiment_summary("pilot_v1")

    print(f"\nExperiment: {summary['experiment_id']}")
    print(f"\nGroup A ({summary['group_a']['user_count']} users):")
    print(f"  Avg vocabulary score: {summary['group_a']['avg_vocabulary_score']:.2f}")
    print(f"  Avg slang usage: {summary['group_a']['avg_slang_usage_rate']:.2%}")

    print(f"\nGroup B ({summary['group_b']['user_count']} users):")
    print(f"  Avg vocabulary score: {summary['group_b']['avg_vocabulary_score']:.2f}")
    print(f"  Avg slang usage: {summary['group_b']['avg_slang_usage_rate']:.2%}")

    print(f"\nComparison:")
    print(f"  Vocabulary: {summary['comparison']['vocabulary_score']['pct_change']:+.1f}%")
    print(f"  Slang usage: {summary['comparison']['slang_usage_rate']['pct_change']:+.1f}%")

    print(f"\nRecommendation: {summary['recommendation']}")


if __name__ == "__main__":
    main()
