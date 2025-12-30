"""
Dataset Formatter Module
Converts classified dialogs into JSONL and CSV formats for LLM fine-tuning.
"""

import json
import csv
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FineTuningExample:
    """A single example for LLM fine-tuning."""
    prompt: str
    completion: str
    metadata: Dict[str, Any]


class DatasetFormatter:
    """Formats classified dialogs for LLM fine-tuning."""

    # Prompt templates for different scenarios
    PROMPT_TEMPLATES = {
        "greetings": [
            "Respond to a greeting in Catalan-accented Spanish:",
            "How would you greet someone in regional Spanish (Catalonia)?",
            "Continue this greeting conversation:",
        ],
        "farewells": [
            "Say goodbye in Catalan-accented Spanish:",
            "How would you end a conversation in regional Spanish?",
            "Respond to someone saying goodbye:",
        ],
        "family": [
            "Talk about family in Catalan-accented Spanish:",
            "Respond to a question about family:",
            "Continue this family conversation:",
        ],
        "emotions": [
            "Express emotions in Catalan-accented Spanish:",
            "How would you express this feeling in regional Spanish?",
            "Respond to someone sharing their feelings:",
        ],
        "opinions": [
            "Share your opinion in Catalan-accented Spanish:",
            "Express agreement or disagreement in regional Spanish:",
            "Continue this discussion with your opinion:",
        ],
        "plans": [
            "Make plans with a friend in Catalan-accented Spanish:",
            "Respond to an invitation in regional Spanish:",
            "Continue this conversation about plans:",
        ],
        "requests": [
            "Ask for help in Catalan-accented Spanish:",
            "Respond to a request in regional Spanish:",
            "Make a polite request:",
        ],
        "apologies": [
            "Apologize in Catalan-accented Spanish:",
            "Respond to an apology in regional Spanish:",
            "Express regret for a mistake:",
        ],
        "small_talk": [
            "Make small talk in Catalan-accented Spanish:",
            "Respond to casual conversation in regional Spanish:",
            "Continue this casual chat:",
        ],
    }

    # System prompts for instruction-tuning
    SYSTEM_PROMPTS = {
        "conversational": """You are a native Spanish speaker from Catalonia.
You speak Castilian Spanish with natural Catalan influence in your vocabulary and expressions.
Respond naturally and conversationally, as a local from Barcelona or the Catalan region would.""",

        "teaching": """You are a Spanish language tutor specializing in Catalan-accented Spanish.
Help learners understand how Spanish is spoken in the Catalonia region, including common expressions
and vocabulary influenced by Catalan.""",

        "roleplay": """You are playing a character from Catalonia in a conversation scenario.
Speak naturally in Catalan-accented Spanish, using regional expressions and vocabulary when appropriate.""",
    }

    def __init__(self, config_path: str = "config/settings.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.output_config = self.config.get('output', {})

    def create_instruction_example(
        self,
        dialog: Dict,
        style: str = "conversational"
    ) -> FineTuningExample:
        """
        Create an instruction-tuning example from a dialog.

        Args:
            dialog: Dialog entry with text, scenario, context
            style: Style of system prompt ('conversational', 'teaching', 'roleplay')
        """
        scenario = dialog.get('scenario', 'small_talk')
        text = dialog['text']
        context_before = dialog.get('context_before', [])

        # Select appropriate prompt template
        templates = self.PROMPT_TEMPLATES.get(scenario, self.PROMPT_TEMPLATES['small_talk'])
        prompt_template = random.choice(templates)

        # Build prompt with context
        if context_before:
            context = " ".join(context_before[-2:])  # Last 2 context lines
            prompt = f"{prompt_template}\n\nContext: {context}\n\nRespond:"
        else:
            prompt = f"{prompt_template}\n\nRespond:"

        # Create metadata
        metadata = {
            "id": dialog.get('id', ''),
            "scenario": scenario,
            "confidence": dialog.get('scenario_confidence', 0.0),
            "source_film": dialog.get('film_title', ''),
            "film_year": dialog.get('film_year', 0),
            "start_timestamp": dialog.get('start_timestamp', ''),
            "end_timestamp": dialog.get('end_timestamp', ''),
            "catalan_markers": dialog.get('catalan_markers', []),
            "system_prompt": self.SYSTEM_PROMPTS.get(style, self.SYSTEM_PROMPTS['conversational'])
        }

        return FineTuningExample(
            prompt=prompt,
            completion=text,
            metadata=metadata
        )

    def create_chat_example(
        self,
        dialog: Dict,
        style: str = "conversational"
    ) -> Dict:
        """
        Create a chat-format example for instruction-tuned models.

        Returns dict in OpenAI/Llama chat format:
        {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}
        """
        scenario = dialog.get('scenario', 'small_talk')
        text = dialog['text']
        context_before = dialog.get('context_before', [])

        system_prompt = self.SYSTEM_PROMPTS.get(style, self.SYSTEM_PROMPTS['conversational'])

        # Build user message
        templates = self.PROMPT_TEMPLATES.get(scenario, self.PROMPT_TEMPLATES['small_talk'])
        user_prompt = random.choice(templates)

        if context_before:
            context = " ".join(context_before[-2:])
            user_message = f"{user_prompt}\n\nContext: {context}"
        else:
            user_message = user_prompt

        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": text}
            ],
            "metadata": {
                "id": dialog.get('id', ''),
                "scenario": scenario,
                "confidence": dialog.get('scenario_confidence', 0.0),
                "source": dialog.get('film_title', ''),
                "catalan_markers": dialog.get('catalan_markers', [])
            }
        }

    def create_conversation_example(
        self,
        dialogs: List[Dict]
    ) -> Dict:
        """
        Create a multi-turn conversation example from sequential dialogs.

        This is useful for teaching conversational flow.
        """
        if not dialogs:
            return {}

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPTS['conversational']}
        ]

        # Alternate between user and assistant roles
        for i, dialog in enumerate(dialogs):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({
                "role": role,
                "content": dialog['text']
            })

        return {
            "messages": messages,
            "metadata": {
                "num_turns": len(dialogs),
                "scenarios": list(set(d.get('scenario', '') for d in dialogs)),
                "source": dialogs[0].get('film_title', '') if dialogs else ''
            }
        }

    def format_for_jsonl(
        self,
        dialogs: List[Dict],
        format_type: str = "chat",
        style: str = "conversational"
    ) -> List[Dict]:
        """
        Format dialogs for JSONL output.

        Args:
            dialogs: List of classified dialog entries
            format_type: 'chat' for chat format, 'instruction' for prompt/completion
            style: System prompt style
        """
        formatted = []

        for dialog in dialogs:
            if format_type == "chat":
                example = self.create_chat_example(dialog, style)
            else:
                ft_example = self.create_instruction_example(dialog, style)
                example = {
                    "prompt": ft_example.prompt,
                    "completion": ft_example.completion,
                    "metadata": ft_example.metadata
                }

            formatted.append(example)

        return formatted

    def format_for_csv(self, dialogs: List[Dict]) -> List[Dict]:
        """
        Format dialogs for CSV output with timestamps.
        """
        csv_rows = []
        columns = self.output_config.get('csv', {}).get('columns', [
            'id', 'text', 'scenario', 'confidence',
            'source_film', 'start_timestamp', 'end_timestamp',
            'context_before', 'context_after', 'catalan_markers'
        ])

        for dialog in dialogs:
            row = {}
            for col in columns:
                if col == 'context_before':
                    row[col] = ' | '.join(dialog.get('context_before', []))
                elif col == 'context_after':
                    row[col] = ' | '.join(dialog.get('context_after', []))
                elif col == 'catalan_markers':
                    row[col] = ', '.join(dialog.get('catalan_markers', []))
                elif col == 'confidence':
                    row[col] = dialog.get('scenario_confidence', 0.0)
                elif col == 'source_film':
                    row[col] = dialog.get('film_title', '')
                else:
                    row[col] = dialog.get(col, '')

            csv_rows.append(row)

        return csv_rows

    def save_jsonl(
        self,
        data: List[Dict],
        output_path: str,
        include_metadata: bool = True
    ):
        """Save data to JSONL format."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data:
                if not include_metadata and 'metadata' in item:
                    # Create copy without metadata
                    item_copy = {k: v for k, v in item.items() if k != 'metadata'}
                    f.write(json.dumps(item_copy, ensure_ascii=False) + '\n')
                else:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')

        logger.info(f"Saved {len(data)} examples to {output_path}")

    def save_csv(self, data: List[Dict], output_path: str):
        """Save data to CSV format."""
        if not data:
            logger.warning("No data to save to CSV")
            return

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        columns = list(data[0].keys())

        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Saved {len(data)} rows to {output_path}")


class EvalSetGenerator:
    """Generates evaluation sets for testing fine-tuned models."""

    def __init__(self, config_path: str = "config/settings.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.eval_config = self.config.get('eval_set', {})
        self.eval_percentage = self.eval_config.get('eval_percentage', 0.15)
        self.balanced = self.eval_config.get('balanced_scenarios', True)
        self.min_per_scenario = self.eval_config.get('min_samples_per_scenario', 50)
        self.seed = self.eval_config.get('random_seed', 42)

    def split_train_eval(
        self,
        dialogs: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Split dialogs into training and evaluation sets.

        If balanced_scenarios is True, ensures equal representation
        of each scenario in the eval set.
        """
        random.seed(self.seed)

        if not self.balanced:
            # Simple random split
            random.shuffle(dialogs)
            split_idx = int(len(dialogs) * (1 - self.eval_percentage))
            return dialogs[:split_idx], dialogs[split_idx:]

        # Balanced split by scenario
        by_scenario = {}
        for dialog in dialogs:
            scenario = dialog.get('scenario', 'unclassified')
            if scenario not in by_scenario:
                by_scenario[scenario] = []
            by_scenario[scenario].append(dialog)

        train_set = []
        eval_set = []

        for scenario, scenario_dialogs in by_scenario.items():
            random.shuffle(scenario_dialogs)

            # Calculate eval samples for this scenario
            eval_count = max(
                self.min_per_scenario,
                int(len(scenario_dialogs) * self.eval_percentage)
            )
            eval_count = min(eval_count, len(scenario_dialogs) // 2)  # Max 50%

            eval_set.extend(scenario_dialogs[:eval_count])
            train_set.extend(scenario_dialogs[eval_count:])

        # Shuffle both sets
        random.shuffle(train_set)
        random.shuffle(eval_set)

        logger.info(f"Split: {len(train_set)} train, {len(eval_set)} eval")
        return train_set, eval_set

    def create_eval_prompts(
        self,
        eval_dialogs: List[Dict],
        num_prompts: int = 100
    ) -> List[Dict]:
        """
        Create evaluation prompts for testing model performance.

        These are prompts without completions, for generating responses
        that can be compared against ground truth.
        """
        formatter = DatasetFormatter()

        # Sample dialogs
        if len(eval_dialogs) > num_prompts:
            sampled = random.sample(eval_dialogs, num_prompts)
        else:
            sampled = eval_dialogs

        eval_prompts = []
        for dialog in sampled:
            example = formatter.create_chat_example(dialog)

            # Remove the assistant response
            messages = example['messages'][:-1]  # System + User only
            ground_truth = example['messages'][-1]['content']

            eval_prompts.append({
                "prompt_id": dialog.get('id', ''),
                "messages": messages,
                "ground_truth": ground_truth,
                "scenario": dialog.get('scenario', ''),
                "metadata": example.get('metadata', {})
            })

        return eval_prompts

    def create_scenario_specific_eval(
        self,
        eval_dialogs: List[Dict],
        scenarios: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Create scenario-specific evaluation sets.

        Useful for testing model performance on specific conversation types.
        """
        if scenarios is None:
            scenarios = list(self.config.get('personal_social_scenarios', {}).keys())

        by_scenario = {s: [] for s in scenarios}

        for dialog in eval_dialogs:
            scenario = dialog.get('scenario', '')
            if scenario in by_scenario:
                by_scenario[scenario].append(dialog)

        # Convert to eval format
        eval_sets = {}
        formatter = DatasetFormatter()

        for scenario, dialogs in by_scenario.items():
            if dialogs:
                eval_sets[scenario] = [
                    formatter.create_chat_example(d)
                    for d in dialogs
                ]

        return eval_sets


def process_dataset(
    classified_dialogs_file: str,
    output_dir: str = "data/processed",
    config_path: str = "config/settings.yaml"
):
    """
    Main function to process classified dialogs into final datasets.

    Creates:
    - Training JSONL file
    - Evaluation JSONL file
    - Full CSV file with timestamps
    - Scenario-specific eval sets
    """
    # Load classified dialogs
    with open(classified_dialogs_file, 'r', encoding='utf-8') as f:
        dialogs = json.load(f)

    logger.info(f"Loaded {len(dialogs)} classified dialogs")

    # Initialize components
    formatter = DatasetFormatter(config_path)
    eval_generator = EvalSetGenerator(config_path)

    # Split into train/eval
    train_dialogs, eval_dialogs = eval_generator.split_train_eval(dialogs)

    # Format for JSONL (chat format)
    train_jsonl = formatter.format_for_jsonl(train_dialogs, format_type="chat")
    eval_jsonl = formatter.format_for_jsonl(eval_dialogs, format_type="chat")

    # Format for CSV
    all_csv = formatter.format_for_csv(dialogs)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save JSONL files
    formatter.save_jsonl(
        train_jsonl,
        str(output_path / "train_catalan_spanish.jsonl")
    )
    formatter.save_jsonl(
        eval_jsonl,
        str(output_path / "eval_catalan_spanish.jsonl")
    )

    # Save CSV
    formatter.save_csv(
        all_csv,
        str(output_path / "catalan_spanish_full.csv")
    )

    # Create eval prompts
    eval_prompts = eval_generator.create_eval_prompts(eval_dialogs)
    with open(output_path / "eval_prompts.json", 'w', encoding='utf-8') as f:
        json.dump(eval_prompts, f, ensure_ascii=False, indent=2)

    # Create scenario-specific evals
    scenario_evals = eval_generator.create_scenario_specific_eval(eval_dialogs)
    for scenario, examples in scenario_evals.items():
        formatter.save_jsonl(
            examples,
            str(output_path / f"eval_{scenario}.jsonl")
        )

    # Print summary
    print("\n" + "=" * 60)
    print("DATASET GENERATION COMPLETE")
    print("=" * 60)
    print(f"Training examples:  {len(train_jsonl)}")
    print(f"Evaluation examples: {len(eval_jsonl)}")
    print(f"Total CSV rows:     {len(all_csv)}")
    print(f"\nOutput directory: {output_dir}")
    print("\nFiles created:")
    print("  - train_catalan_spanish.jsonl")
    print("  - eval_catalan_spanish.jsonl")
    print("  - catalan_spanish_full.csv")
    print("  - eval_prompts.json")
    for scenario in scenario_evals.keys():
        print(f"  - eval_{scenario}.jsonl")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "data/processed"

        process_dataset(input_file, output_dir)
    else:
        print("Usage: python dataset_formatter.py <classified_dialogs.json> [output_dir]")
