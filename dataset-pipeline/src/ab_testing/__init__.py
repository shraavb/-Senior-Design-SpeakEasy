"""
A/B Testing Module for SpeakEasy Fine-Tuning Experiments.

This module provides tools for running A/B tests comparing different
fine-tuning approaches and tracking learning outcomes.
"""

from .experiment_config import (
    Experiment,
    ExperimentConfig,
    get_experiment,
    list_experiments,
)
from .user_assignment import assign_user_to_group
from .metrics_collector import MetricsCollector

__all__ = [
    "Experiment",
    "ExperimentConfig",
    "get_experiment",
    "list_experiments",
    "assign_user_to_group",
    "MetricsCollector",
]
