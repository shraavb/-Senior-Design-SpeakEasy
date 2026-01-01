"""
Ground truth data loader.

Loads dialogue data from the dataset pipeline for comparison and evaluation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class GroundTruthLoader:
    """
    Loader for ground truth dialogue data.

    Provides access to:
    - Dialogue transcripts
    - Expected vocabulary by scenario
    - CEFR-classified examples
    - Assessment rubrics
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the loader.

        Args:
            data_dir: Path to data/eval directory
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent.parent.parent / "data" / "eval"

        self._dialogues = None
        self._vocabulary = None
        self._rubrics = None

    @property
    def dialogues(self) -> Dict[str, Any]:
        """Load dialogues on first access."""
        if self._dialogues is None:
            self._dialogues = self._load_dialogues()
        return self._dialogues

    @property
    def vocabulary(self) -> Dict[str, Any]:
        """Load vocabulary on first access."""
        if self._vocabulary is None:
            self._vocabulary = self._load_vocabulary()
        return self._vocabulary

    @property
    def rubrics(self) -> Dict[str, Any]:
        """Load rubrics on first access."""
        if self._rubrics is None:
            self._rubrics = self._load_rubrics()
        return self._rubrics

    def _load_dialogues(self) -> Dict[str, List[Dict]]:
        """Load dialogue data organized by level."""
        dialogues = {"beginner": [], "intermediate": [], "advanced": [], "mastery": []}

        # Try to load CEFR-classified dialogues
        cefr_file = self.data_dir / "dialogues_by_complexity_cefr.json"
        if cefr_file.exists():
            try:
                with open(cefr_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for level in dialogues.keys():
                        if level in data:
                            dialogues[level] = data[level]
                logger.info(f"Loaded {sum(len(v) for v in dialogues.values())} dialogues")
            except Exception as e:
                logger.error(f"Failed to load dialogues: {e}")

        # Fallback to merged eval file
        if not any(dialogues.values()):
            merged_file = self.data_dir / "dialogues_merged_eval.json"
            if merged_file.exists():
                try:
                    with open(merged_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Organize by simplified level
                        for item in data:
                            level = item.get("cefr_simplified", "intermediate")
                            if level in dialogues:
                                dialogues[level].append(item)
                except Exception as e:
                    logger.error(f"Failed to load merged dialogues: {e}")

        return dialogues

    def _load_vocabulary(self) -> Dict[str, Dict]:
        """Load scenario vocabulary."""
        vocab_file = self.data_dir / "scenario_vocabulary.json"
        if vocab_file.exists():
            try:
                with open(vocab_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load vocabulary: {e}")

        return {}

    def _load_rubrics(self) -> Dict[str, Any]:
        """Load assessment rubrics."""
        rubrics_file = self.data_dir / "user_assessment_rubrics.json"
        if rubrics_file.exists():
            try:
                with open(rubrics_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load rubrics: {e}")

        return {}

    def get_dialogue_by_id(self, dialogue_id: str) -> Optional[Dict]:
        """Get a specific dialogue by ID."""
        for level_dialogues in self.dialogues.values():
            for dialogue in level_dialogues:
                if dialogue.get("id") == dialogue_id:
                    return dialogue
        return None

    def get_dialogues_by_scenario(
        self,
        scenario: str,
        level: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get dialogues for a specific scenario.

        Args:
            scenario: Scenario type (greetings, farewells, etc.)
            level: Optional CEFR level filter

        Returns:
            List of matching dialogues
        """
        results = []

        levels_to_check = [level] if level else self.dialogues.keys()

        for lvl in levels_to_check:
            for dialogue in self.dialogues.get(lvl, []):
                if dialogue.get("scenario", "").lower() == scenario.lower():
                    results.append(dialogue)

        return results

    def get_expected_vocabulary(self, scenario: str) -> Dict[str, List[str]]:
        """
        Get expected vocabulary for a scenario.

        Returns:
            Dictionary with beginner, intermediate, advanced, catalan_regional lists
        """
        return self.vocabulary.get(scenario, {
            "beginner": [],
            "intermediate": [],
            "advanced": [],
            "catalan_regional": [],
        })

    def get_rubric_for_level(self, level: str) -> Dict[str, Any]:
        """Get assessment rubric for CEFR level."""
        return self.rubrics.get(level, self.rubrics.get("B1", {}))

    def get_random_dialogue(
        self,
        level: str = "intermediate",
        scenario: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Get a random dialogue for practice.

        Args:
            level: CEFR level (beginner, intermediate, advanced, mastery)
            scenario: Optional scenario filter

        Returns:
            Random dialogue or None
        """
        import random

        candidates = self.dialogues.get(level, [])

        if scenario:
            candidates = [d for d in candidates if d.get("scenario") == scenario]

        if candidates:
            return random.choice(candidates)

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded data."""
        return {
            "total_dialogues": sum(len(v) for v in self.dialogues.values()),
            "dialogues_by_level": {k: len(v) for k, v in self.dialogues.items()},
            "scenarios_with_vocabulary": list(self.vocabulary.keys()),
            "rubrics_available": list(self.rubrics.keys()),
        }


# Singleton instance
_loader_instance: Optional[GroundTruthLoader] = None


def get_ground_truth_loader(data_dir: Optional[str] = None) -> GroundTruthLoader:
    """Get or create singleton ground truth loader."""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = GroundTruthLoader(data_dir)
    return _loader_instance


@lru_cache(maxsize=100)
def get_expected_response(dialogue_id: str) -> Optional[str]:
    """
    Get expected response for a dialogue (cached).

    Args:
        dialogue_id: Dialogue identifier

    Returns:
        Expected response text or None
    """
    loader = get_ground_truth_loader()
    dialogue = loader.get_dialogue_by_id(dialogue_id)

    if dialogue:
        # Return the full dialogue text or last speaker's line
        if "conversation" in dialogue:
            return " ".join(
                turn.get("text", "") for turn in dialogue["conversation"]
            )
        return dialogue.get("text", dialogue.get("ground_truth", ""))

    return None
