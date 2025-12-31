#!/usr/bin/env python3
"""
A/B Testing Experiment Configuration.

This module defines experiments comparing different fine-tuning approaches
for the SpeakEasy Catalan-Spanish language learning platform.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum


class ApproachType(Enum):
    """Fine-tuning approach types."""
    BASELINE = "baseline"           # No fine-tuning, prompt engineering only
    LORA_ONLY = "lora_only"         # Approach 1: Direct LoRA fine-tuning
    TOKENIZER_EXPANSION = "tokenizer_expansion"  # Approach 2: Full pipeline
    SLANG_AUGMENTED = "slang_augmented"  # Approach 3: LoRA + synthetic slang
    DPO = "dpo"                     # Approach 5: Direct Preference Optimization


@dataclass
class Approach:
    """Definition of a fine-tuning approach."""
    id: str
    name: str
    type: ApproachType
    description: str
    model_path: Optional[str] = None
    training_data: Optional[str] = None
    training_time_hours: Optional[float] = None
    config: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        result = asdict(self)
        result['type'] = self.type.value
        return result


@dataclass
class Experiment:
    """Definition of an A/B test experiment."""
    id: str
    name: str
    description: str
    hypothesis: str
    approach_a: Approach
    approach_b: Approach
    status: str = "draft"  # draft, active, completed, cancelled
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    target_users: int = 10
    metrics_tracked: List[str] = field(default_factory=list)
    results: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "hypothesis": self.hypothesis,
            "approach_a": self.approach_a.to_dict(),
            "approach_b": self.approach_b.to_dict(),
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "target_users": self.target_users,
            "metrics_tracked": self.metrics_tracked,
            "results": self.results,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


# ============================================================================
# PREDEFINED APPROACHES
# ============================================================================

APPROACHES = {
    "baseline": Approach(
        id="baseline",
        name="Baseline (No Fine-tuning)",
        type=ApproachType.BASELINE,
        description="Base Llama model with prompt engineering only. Control group.",
        model_path="meta-llama/Llama-3.2-1B",
        training_data=None,
        training_time_hours=0,
        config={"use_prompt_engineering": True},
    ),
    "lora_only": Approach(
        id="lora_only",
        name="LoRA Fine-tuning Only",
        type=ApproachType.LORA_ONLY,
        description="Direct LoRA fine-tuning on conversation data (Approach 1).",
        model_path="models/approach1-lora-only",
        training_data="data/processed/train_catalan_spanish.jsonl",
        training_time_hours=3,
        config={
            "lora_r": 64,
            "lora_alpha": 16,
            "epochs": 3,
            "learning_rate": 2e-4,
        },
    ),
    "tokenizer_expansion": Approach(
        id="tokenizer_expansion",
        name="Tokenizer Expansion + Pre-training + LoRA",
        type=ApproachType.TOKENIZER_EXPANSION,
        description="Full pipeline with tokenizer expansion for deep dialect specialization (Approach 2).",
        model_path="models/approach2-step2-pretrained",
        training_data="data/processed/train_catalan_spanish.jsonl",
        training_time_hours=12,
        config={
            "new_tokens": 21,
            "pretrain_epochs": 2,
            "finetune_epochs": 3,
        },
    ),
    "slang_augmented": Approach(
        id="slang_augmented",
        name="Slang-Augmented LoRA",
        type=ApproachType.SLANG_AUGMENTED,
        description="LoRA fine-tuning with additional synthetic slang examples (Approach 3).",
        model_path="models/slang-augmented-lora",
        training_data="data/processed/slang_filtered/train_with_slang_augmented.jsonl",
        training_time_hours=3.5,
        config={
            "lora_r": 64,
            "lora_alpha": 16,
            "epochs": 3,
            "synthetic_examples": 70,
            "original_examples": 11524,
        },
    ),
}

# ============================================================================
# PREDEFINED EXPERIMENTS
# ============================================================================

EXPERIMENTS = {
    "pilot_v1": Experiment(
        id="pilot_v1",
        name="Pilot: LoRA vs Slang-Augmented",
        description="Initial pilot comparing standard LoRA fine-tuning against slang-augmented training data.",
        hypothesis="Slang-augmented training will produce more authentic regional language use and higher user engagement.",
        approach_a=APPROACHES["lora_only"],
        approach_b=APPROACHES["slang_augmented"],
        status="draft",
        target_users=10,
        metrics_tracked=[
            "vocabulary_score",
            "slang_usage_rate",
            "regional_authenticity",
            "user_engagement_time",
            "completion_rate",
            "self_reported_confidence",
            "cefr_level_progression",
        ],
    ),
    "pilot_v2": Experiment(
        id="pilot_v2",
        name="Pilot: Baseline vs LoRA",
        description="Compare no fine-tuning (prompt engineering) against LoRA fine-tuning.",
        hypothesis="Fine-tuning will significantly outperform prompt engineering for dialect authenticity.",
        approach_a=APPROACHES["baseline"],
        approach_b=APPROACHES["lora_only"],
        status="draft",
        target_users=10,
        metrics_tracked=[
            "vocabulary_score",
            "regional_authenticity",
            "scenario_appropriateness",
            "user_satisfaction",
        ],
    ),
    "full_comparison": Experiment(
        id="full_comparison",
        name="Full Approach Comparison",
        description="Comprehensive comparison of all approaches after pilot validation.",
        hypothesis="Tokenizer expansion will provide best regional authenticity; slang augmentation will best balance quality and training cost.",
        approach_a=APPROACHES["lora_only"],
        approach_b=APPROACHES["tokenizer_expansion"],
        status="draft",
        target_users=50,
        metrics_tracked=[
            "vocabulary_score",
            "slang_usage_rate",
            "bleu_score",
            "semantic_similarity",
            "regional_authenticity",
            "grammar_score",
            "cefr_level",
            "user_engagement_time",
            "completion_rate",
            "return_visits",
            "self_reported_confidence",
            "nps_score",
        ],
    ),
}


# ============================================================================
# CONFIGURATION CLASS
# ============================================================================

class ExperimentConfig:
    """
    Manages experiment configurations and persistence.

    Usage:
        config = ExperimentConfig()
        experiment = config.get_experiment("pilot_v1")
        config.activate_experiment("pilot_v1")
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize experiment configuration.

        Args:
            config_dir: Directory for storing experiment configs and results
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(__file__).parent.parent.parent / "data" / "experiments"

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.experiments = dict(EXPERIMENTS)
        self.approaches = dict(APPROACHES)

        # Load any saved experiments
        self._load_experiments()

    def _load_experiments(self) -> None:
        """Load experiments from config directory."""
        config_file = self.config_dir / "experiments.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Update experiment status from saved data
                    for exp_id, exp_data in data.items():
                        if exp_id in self.experiments:
                            self.experiments[exp_id].status = exp_data.get("status", "draft")
                            self.experiments[exp_id].start_date = exp_data.get("start_date")
                            self.experiments[exp_id].end_date = exp_data.get("end_date")
                            self.experiments[exp_id].results = exp_data.get("results")
            except Exception as e:
                print(f"Warning: Could not load experiments: {e}")

    def save_experiments(self) -> None:
        """Save experiments to config directory."""
        config_file = self.config_dir / "experiments.json"
        data = {exp_id: exp.to_dict() for exp_id, exp in self.experiments.items()}
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID."""
        return self.experiments.get(experiment_id)

    def list_experiments(self) -> List[Experiment]:
        """List all experiments."""
        return list(self.experiments.values())

    def get_active_experiment(self) -> Optional[Experiment]:
        """Get the currently active experiment."""
        for exp in self.experiments.values():
            if exp.status == "active":
                return exp
        return None

    def activate_experiment(self, experiment_id: str) -> bool:
        """
        Activate an experiment.

        Args:
            experiment_id: ID of experiment to activate

        Returns:
            True if successful
        """
        if experiment_id not in self.experiments:
            return False

        # Deactivate any currently active experiment
        for exp in self.experiments.values():
            if exp.status == "active":
                exp.status = "paused"

        self.experiments[experiment_id].status = "active"
        self.experiments[experiment_id].start_date = datetime.now().isoformat()
        self.save_experiments()
        return True

    def complete_experiment(self, experiment_id: str, results: Dict) -> bool:
        """
        Mark experiment as completed with results.

        Args:
            experiment_id: ID of experiment
            results: Experiment results dict

        Returns:
            True if successful
        """
        if experiment_id not in self.experiments:
            return False

        self.experiments[experiment_id].status = "completed"
        self.experiments[experiment_id].end_date = datetime.now().isoformat()
        self.experiments[experiment_id].results = results
        self.save_experiments()
        return True

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        description: str,
        hypothesis: str,
        approach_a_id: str,
        approach_b_id: str,
        target_users: int = 10,
        metrics: Optional[List[str]] = None,
    ) -> Experiment:
        """
        Create a new experiment.

        Args:
            experiment_id: Unique ID
            name: Display name
            description: Experiment description
            hypothesis: What we're testing
            approach_a_id: ID of first approach
            approach_b_id: ID of second approach
            target_users: Number of users to test
            metrics: List of metrics to track

        Returns:
            Created Experiment object
        """
        if approach_a_id not in self.approaches or approach_b_id not in self.approaches:
            raise ValueError("Invalid approach ID")

        experiment = Experiment(
            id=experiment_id,
            name=name,
            description=description,
            hypothesis=hypothesis,
            approach_a=self.approaches[approach_a_id],
            approach_b=self.approaches[approach_b_id],
            target_users=target_users,
            metrics_tracked=metrics or [],
        )

        self.experiments[experiment_id] = experiment
        self.save_experiments()
        return experiment


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_experiment(experiment_id: str) -> Optional[Experiment]:
    """Get experiment by ID (convenience function)."""
    config = ExperimentConfig()
    return config.get_experiment(experiment_id)


def list_experiments() -> List[Experiment]:
    """List all experiments (convenience function)."""
    config = ExperimentConfig()
    return config.list_experiments()


def main():
    """Test experiment configuration."""
    print("A/B Testing Experiment Configuration")
    print("=" * 50)

    config = ExperimentConfig()

    print("\nAvailable Approaches:")
    for approach_id, approach in config.approaches.items():
        print(f"  - {approach_id}: {approach.name}")

    print("\nDefined Experiments:")
    for exp in config.list_experiments():
        print(f"\n  {exp.id}: {exp.name}")
        print(f"    Status: {exp.status}")
        print(f"    A: {exp.approach_a.name}")
        print(f"    B: {exp.approach_b.name}")
        print(f"    Hypothesis: {exp.hypothesis[:60]}...")

    print("\n" + "=" * 50)
    print("Recommended first experiment: pilot_v1")
    print("  Tests: LoRA Only vs Slang-Augmented LoRA")
    print("  This validates whether slang augmentation improves learning outcomes.")


if __name__ == "__main__":
    main()
