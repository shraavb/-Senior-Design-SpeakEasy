#!/usr/bin/env python3
"""
User Assignment for A/B Testing.

This module handles deterministic assignment of users to experiment groups
to ensure consistent experience across sessions.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class UserAssignment:
    """Record of a user's experiment assignment."""
    user_id: str
    experiment_id: str
    group: str  # "A" or "B"
    assigned_at: str
    approach_id: str


class UserAssignmentManager:
    """
    Manages user assignments to experiment groups.

    Uses deterministic hashing to ensure users always get the same group
    for a given experiment, even across sessions.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize assignment manager.

        Args:
            storage_path: Path to store assignment records (JSON file)
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = (
                Path(__file__).parent.parent.parent /
                "data" / "experiments" / "user_assignments.json"
            )

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.assignments: Dict[str, UserAssignment] = {}
        self._load_assignments()

    def _load_assignments(self) -> None:
        """Load assignments from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, record in data.items():
                        self.assignments[key] = UserAssignment(**record)
            except Exception as e:
                print(f"Warning: Could not load assignments: {e}")

    def _save_assignments(self) -> None:
        """Save assignments to storage."""
        data = {key: asdict(record) for key, record in self.assignments.items()}
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_assignment_key(self, user_id: str, experiment_id: str) -> str:
        """Generate unique key for user-experiment pair."""
        return f"{user_id}:{experiment_id}"

    def assign_user(
        self,
        user_id: str,
        experiment_id: str,
        approach_a_id: str,
        approach_b_id: str,
    ) -> UserAssignment:
        """
        Assign a user to an experiment group.

        Uses deterministic hashing so the same user always gets the same group.

        Args:
            user_id: Unique user identifier
            experiment_id: Experiment being assigned to
            approach_a_id: ID of approach A
            approach_b_id: ID of approach B

        Returns:
            UserAssignment record
        """
        key = self._get_assignment_key(user_id, experiment_id)

        # Check if already assigned
        if key in self.assignments:
            return self.assignments[key]

        # Deterministic assignment based on hash
        group = assign_user_to_group(user_id, experiment_id)
        approach_id = approach_a_id if group == "A" else approach_b_id

        assignment = UserAssignment(
            user_id=user_id,
            experiment_id=experiment_id,
            group=group,
            assigned_at=datetime.now().isoformat(),
            approach_id=approach_id,
        )

        self.assignments[key] = assignment
        self._save_assignments()

        return assignment

    def get_assignment(
        self,
        user_id: str,
        experiment_id: str
    ) -> Optional[UserAssignment]:
        """
        Get existing assignment for user.

        Args:
            user_id: User identifier
            experiment_id: Experiment ID

        Returns:
            UserAssignment if exists, None otherwise
        """
        key = self._get_assignment_key(user_id, experiment_id)
        return self.assignments.get(key)

    def get_users_in_group(
        self,
        experiment_id: str,
        group: str
    ) -> List[UserAssignment]:
        """
        Get all users assigned to a specific group.

        Args:
            experiment_id: Experiment ID
            group: "A" or "B"

        Returns:
            List of UserAssignment records
        """
        return [
            assignment for assignment in self.assignments.values()
            if assignment.experiment_id == experiment_id
            and assignment.group == group
        ]

    def get_experiment_stats(self, experiment_id: str) -> Dict:
        """
        Get assignment statistics for an experiment.

        Args:
            experiment_id: Experiment ID

        Returns:
            Dict with group counts and balance info
        """
        group_a = self.get_users_in_group(experiment_id, "A")
        group_b = self.get_users_in_group(experiment_id, "B")

        total = len(group_a) + len(group_b)
        balance = abs(len(group_a) - len(group_b)) / total if total > 0 else 0

        return {
            "experiment_id": experiment_id,
            "total_users": total,
            "group_a_count": len(group_a),
            "group_b_count": len(group_b),
            "balance_ratio": 1 - balance,  # 1.0 = perfectly balanced
            "group_a_users": [a.user_id for a in group_a],
            "group_b_users": [a.user_id for a in group_b],
        }


def assign_user_to_group(user_id: str, experiment_id: str) -> str:
    """
    Deterministically assign user to group A or B.

    Uses MD5 hash of user_id + experiment_id to ensure:
    - Same user always gets same group for same experiment
    - Different experiments can have different assignments
    - Approximately 50/50 split

    Args:
        user_id: Unique user identifier
        experiment_id: Experiment identifier

    Returns:
        "A" or "B"
    """
    hash_input = f"{user_id}:{experiment_id}"
    hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
    return "A" if hash_value % 2 == 0 else "B"


def main():
    """Test user assignment."""
    print("Testing User Assignment")
    print("=" * 50)

    # Test deterministic assignment
    test_users = ["user_001", "user_002", "user_003", "user_004", "user_005"]
    experiment = "pilot_v1"

    print(f"\nAssignments for experiment '{experiment}':")
    for user_id in test_users:
        group = assign_user_to_group(user_id, experiment)
        print(f"  {user_id} -> Group {group}")

    # Test that assignments are deterministic
    print("\nVerifying determinism (same user, same experiment):")
    for user_id in test_users[:2]:
        g1 = assign_user_to_group(user_id, experiment)
        g2 = assign_user_to_group(user_id, experiment)
        g3 = assign_user_to_group(user_id, experiment)
        print(f"  {user_id}: {g1}, {g2}, {g3} (all same: {g1 == g2 == g3})")

    # Test different experiments
    print("\nSame user, different experiments:")
    user = "user_001"
    for exp in ["pilot_v1", "pilot_v2", "full_comparison"]:
        group = assign_user_to_group(user, exp)
        print(f"  {user} in {exp} -> Group {group}")

    # Test manager
    print("\n" + "=" * 50)
    print("Testing UserAssignmentManager")

    manager = UserAssignmentManager()

    for user_id in test_users:
        assignment = manager.assign_user(
            user_id=user_id,
            experiment_id="pilot_v1",
            approach_a_id="lora_only",
            approach_b_id="slang_augmented",
        )
        print(f"  {user_id} -> Group {assignment.group} ({assignment.approach_id})")

    stats = manager.get_experiment_stats("pilot_v1")
    print(f"\nExperiment Stats:")
    print(f"  Total users: {stats['total_users']}")
    print(f"  Group A: {stats['group_a_count']}")
    print(f"  Group B: {stats['group_b_count']}")
    print(f"  Balance: {stats['balance_ratio']:.2%}")


if __name__ == "__main__":
    main()
