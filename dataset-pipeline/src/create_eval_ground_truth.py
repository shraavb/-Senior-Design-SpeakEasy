#!/usr/bin/env python3
"""
Create Ground Truth Evaluation Sets
Generates structured evaluation data for both model and user assessment.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
import csv

# Scenario-specific expected vocabulary (ground truth for user evaluation)
SCENARIO_VOCABULARY = {
    "greetings": {
        "beginner": ["hola", "buenos días", "buenas tardes", "buenas noches"],
        "intermediate": ["qué tal", "cómo estás", "encantado", "mucho gusto"],
        "advanced": ["qué hay", "cómo va", "un placer", "igualmente"],
        "catalan_regional": ["ei", "apa", "home", "buenas"]  # Catalan-influenced
    },
    "farewells": {
        "beginner": ["adiós", "hasta luego", "chao"],
        "intermediate": ["nos vemos", "hasta pronto", "hasta mañana"],
        "advanced": ["cuídate", "que te vaya bien", "ya nos veremos"],
        "catalan_regional": ["apa", "adéu", "a reveure"]
    },
    "family": {
        "beginner": ["mamá", "papá", "hermano", "hermana"],
        "intermediate": ["familia", "padres", "hijos", "abuelos"],
        "advanced": ["parientes", "suegros", "cuñado", "sobrino"],
        "catalan_regional": ["nena", "nen", "avi", "iaia"]
    },
    "emotions": {
        "beginner": ["feliz", "triste", "bien", "mal"],
        "intermediate": ["contento", "preocupado", "enfadado", "nervioso"],
        "advanced": ["emocionado", "agotado", "aliviado", "frustrado"],
        "catalan_regional": ["flipar", "molar", "estar rallat"]
    },
    "opinions": {
        "beginner": ["sí", "no", "me gusta", "no me gusta"],
        "intermediate": ["creo que", "pienso que", "me parece"],
        "advanced": ["estoy de acuerdo", "no estoy de acuerdo", "en mi opinión"],
        "catalan_regional": ["home", "ostras", "collons"]
    },
    "plans": {
        "beginner": ["quiero", "vamos", "mañana"],
        "intermediate": ["quedamos", "te apetece", "este fin de semana"],
        "advanced": ["sería posible", "qué te parece si", "tengo previsto"],
        "catalan_regional": ["apa va", "va", "fem"]
    },
    "requests": {
        "beginner": ["por favor", "gracias", "ayuda"],
        "intermediate": ["puedes", "podrías", "necesito"],
        "advanced": ["te importaría", "sería posible", "me harías el favor"],
        "catalan_regional": ["si us plau", "home", "escolta"]
    },
    "apologies": {
        "beginner": ["perdón", "lo siento"],
        "intermediate": ["perdona", "disculpa", "fue mi culpa"],
        "advanced": ["no era mi intención", "lamento mucho", "te pido disculpas"],
        "catalan_regional": ["home, perdona", "ostras, perdona"]
    },
    "small_talk": {
        "beginner": ["qué tiempo", "hace calor", "hace frío"],
        "intermediate": ["qué tal el trabajo", "cómo va todo"],
        "advanced": ["qué hay de nuevo", "cómo te va la vida"],
        "catalan_regional": ["nen", "nena", "home"]
    }
}

# CEFR-aligned proficiency rubrics
CEFR_RUBRICS = {
    "A1": {
        "description": "Can use basic greetings and simple phrases",
        "criteria": [
            "Uses basic vocabulary correctly",
            "Responds appropriately to simple prompts",
            "May have frequent grammatical errors"
        ],
        "min_vocabulary_score": 1,
        "max_vocabulary_score": 3
    },
    "A2": {
        "description": "Can handle simple social exchanges",
        "criteria": [
            "Uses intermediate vocabulary",
            "Maintains basic conversation flow",
            "Grammar errors don't impede understanding"
        ],
        "min_vocabulary_score": 3,
        "max_vocabulary_score": 6
    },
    "B1": {
        "description": "Can deal with most social situations",
        "criteria": [
            "Uses varied vocabulary appropriately",
            "Can express opinions and feelings",
            "Generally good grammar with occasional errors"
        ],
        "min_vocabulary_score": 6,
        "max_vocabulary_score": 10
    },
    "B2": {
        "description": "Can interact fluently with native speakers",
        "criteria": [
            "Uses advanced and regional vocabulary",
            "Natural conversational flow",
            "Few grammatical errors"
        ],
        "min_vocabulary_score": 10,
        "max_vocabulary_score": 15
    }
}


def load_classified_dialogs(filepath: str) -> List[Dict]:
    """Load classified dialogs from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_model_eval_set(
    dialogs: List[Dict],
    samples_per_scenario: int = 20,
    seed: int = 42
) -> List[Dict]:
    """
    Create evaluation set for model quality assessment.

    Each item contains:
    - prompt: The input to give the model
    - ground_truth: The expected response (from subtitles)
    - scenario: The conversation type
    - context: Surrounding dialog for reference
    """
    random.seed(seed)

    # Group by scenario
    by_scenario = defaultdict(list)
    for dialog in dialogs:
        scenario = dialog.get('scenario', 'unknown')
        if scenario != 'unknown' and dialog.get('scenario_confidence', 0) > 0.7:
            by_scenario[scenario].append(dialog)

    eval_set = []

    for scenario, scenario_dialogs in by_scenario.items():
        # Sample dialogs
        sampled = random.sample(
            scenario_dialogs,
            min(samples_per_scenario, len(scenario_dialogs))
        )

        for dialog in sampled:
            # Create prompt based on scenario
            prompt = _create_scenario_prompt(scenario, dialog)

            eval_item = {
                "id": dialog.get('id', ''),
                "scenario": scenario,
                "prompt": prompt,
                "ground_truth": dialog['text'],
                "context_before": dialog.get('context_before', []),
                "context_after": dialog.get('context_after', []),
                "source_film": dialog.get('film_title', ''),
                "timestamp": dialog.get('start_timestamp', ''),
                "expected_vocabulary": SCENARIO_VOCABULARY.get(scenario, {}),
                "confidence": dialog.get('scenario_confidence', 0)
            }
            eval_set.append(eval_item)

    return eval_set


def _create_scenario_prompt(scenario: str, dialog: Dict) -> str:
    """Create an appropriate prompt for the scenario."""
    context = dialog.get('context_before', [])
    context_str = " ".join(context[-2:]) if context else ""

    prompts = {
        "greetings": f"Respond to a greeting in Catalan-accented Spanish.\nContext: {context_str}",
        "farewells": f"Say goodbye appropriately in regional Spanish.\nContext: {context_str}",
        "family": f"Continue this family conversation in Catalan-accented Spanish.\nContext: {context_str}",
        "emotions": f"Express your feelings in regional Spanish.\nContext: {context_str}",
        "opinions": f"Share your opinion in Catalan-accented Spanish.\nContext: {context_str}",
        "plans": f"Make or respond to plans in regional Spanish.\nContext: {context_str}",
        "requests": f"Make a polite request in Catalan-accented Spanish.\nContext: {context_str}",
        "apologies": f"Apologize appropriately in regional Spanish.\nContext: {context_str}",
        "small_talk": f"Continue this casual conversation in Catalan-accented Spanish.\nContext: {context_str}",
    }

    return prompts.get(scenario, f"Respond in Catalan-accented Spanish.\nContext: {context_str}")


def create_user_eval_rubric(scenario: str) -> Dict:
    """
    Create evaluation rubric for assessing user responses.

    Returns scoring criteria for a given scenario.
    """
    vocab = SCENARIO_VOCABULARY.get(scenario, {})

    rubric = {
        "scenario": scenario,
        "vocabulary_checklist": {
            "beginner_words": vocab.get("beginner", []),
            "intermediate_words": vocab.get("intermediate", []),
            "advanced_words": vocab.get("advanced", []),
            "regional_markers": vocab.get("catalan_regional", [])
        },
        "scoring": {
            "beginner_word": 1,
            "intermediate_word": 2,
            "advanced_word": 3,
            "regional_marker": 4,  # Bonus for using regional expressions
        },
        "grammar_criteria": [
            "Subject-verb agreement",
            "Correct verb tense",
            "Proper gender/number agreement",
            "Appropriate formality level (tú/usted)"
        ],
        "fluency_criteria": [
            "Natural word order",
            "Appropriate response length",
            "Contextually relevant",
            "Conversation flow maintained"
        ],
        "cefr_mapping": CEFR_RUBRICS
    }

    return rubric


def create_crowdsourcing_task(eval_set: List[Dict], output_path: str):
    """
    Create a CSV file formatted for crowdsourcing platforms (Prolific, MTurk).

    Evaluators will rate model outputs on multiple dimensions.
    """
    fieldnames = [
        "task_id",
        "scenario",
        "prompt",
        "model_response",  # To be filled with model output
        "ground_truth_response",
        "source_film",

        # Rating fields (1-5 scale)
        "naturalness_rating",
        "regional_authenticity_rating",
        "scenario_appropriateness_rating",
        "grammar_rating",

        # Open feedback
        "evaluator_notes"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, item in enumerate(eval_set):
            row = {
                "task_id": f"eval_{i:04d}",
                "scenario": item["scenario"],
                "prompt": item["prompt"],
                "model_response": "",  # Fill after running model
                "ground_truth_response": item["ground_truth"],
                "source_film": item.get("source_film", ""),
                "naturalness_rating": "",
                "regional_authenticity_rating": "",
                "scenario_appropriateness_rating": "",
                "grammar_rating": "",
                "evaluator_notes": ""
            }
            writer.writerow(row)

    print(f"Created crowdsourcing task file: {output_path}")
    print(f"  - {len(eval_set)} items to evaluate")
    print(f"  - Upload to Prolific/MTurk after filling model_response column")


def create_user_assessment_template(output_path: str):
    """
    Create assessment templates for evaluating learner responses.
    """
    assessments = []

    for scenario, vocab in SCENARIO_VOCABULARY.items():
        rubric = create_user_eval_rubric(scenario)

        # Create sample assessment prompts
        assessment = {
            "scenario": scenario,
            "sample_prompts": _get_sample_prompts(scenario),
            "rubric": rubric,
            "scoring_guide": {
                "0-3 points": "A1 - Basic",
                "4-6 points": "A2 - Elementary",
                "7-10 points": "B1 - Intermediate",
                "11-15 points": "B2 - Upper Intermediate",
                "16+ points": "C1 - Advanced (with regional markers)"
            }
        }
        assessments.append(assessment)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(assessments, f, ensure_ascii=False, indent=2)

    print(f"Created user assessment template: {output_path}")


def _get_sample_prompts(scenario: str) -> List[str]:
    """Get sample assessment prompts for a scenario."""
    prompts = {
        "greetings": [
            "You meet a friend on the street. Greet them.",
            "You arrive at a job interview. Introduce yourself.",
            "You're at a party and someone introduces themselves to you."
        ],
        "farewells": [
            "You're leaving a friend's house after dinner.",
            "You're ending a phone call with a colleague.",
            "You're saying goodbye at the airport."
        ],
        "family": [
            "Describe your family to a new friend.",
            "Tell someone about your weekend plans with family.",
            "Ask about someone's family."
        ],
        "emotions": [
            "You just got great news. Express your happiness.",
            "You're worried about an exam. Express your concern.",
            "You're frustrated with traffic. Express your frustration."
        ],
        "opinions": [
            "Share your opinion about a movie you watched.",
            "Agree or disagree with a friend's restaurant choice.",
            "Express your view on a current topic."
        ],
        "plans": [
            "Invite a friend to dinner this weekend.",
            "Suggest plans for a Saturday afternoon.",
            "Respond to an invitation to go hiking."
        ],
        "requests": [
            "Ask a stranger for directions.",
            "Ask a colleague to help with a project.",
            "Request a table at a restaurant."
        ],
        "apologies": [
            "You're late to a meeting. Apologize.",
            "You accidentally bumped into someone.",
            "You forgot a friend's birthday."
        ],
        "small_talk": [
            "Comment on the weather to a neighbor.",
            "Ask a colleague about their weekend.",
            "Make conversation while waiting in line."
        ]
    }
    return prompts.get(scenario, ["Respond appropriately in Spanish."])


def main():
    """Generate all evaluation ground truth files."""

    # Paths
    input_path = "data/processed/classified_dialogs.json"
    output_dir = Path("data/eval")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("CREATING EVALUATION GROUND TRUTH")
    print("=" * 60)

    # Load data
    print("\nLoading classified dialogs...")
    dialogs = load_classified_dialogs(input_path)
    print(f"Loaded {len(dialogs)} dialogs")

    # 1. Create model evaluation set
    print("\n1. Creating model evaluation set...")
    model_eval = create_model_eval_set(dialogs, samples_per_scenario=25)

    with open(output_dir / "model_eval_ground_truth.json", 'w', encoding='utf-8') as f:
        json.dump(model_eval, f, ensure_ascii=False, indent=2)
    print(f"   Created {len(model_eval)} model evaluation items")

    # 2. Create crowdsourcing task file
    print("\n2. Creating crowdsourcing task template...")
    create_crowdsourcing_task(model_eval, str(output_dir / "crowdsourcing_task.csv"))

    # 3. Create user assessment rubrics
    print("\n3. Creating user assessment rubrics...")
    create_user_assessment_template(str(output_dir / "user_assessment_rubrics.json"))

    # 4. Create vocabulary ground truth
    print("\n4. Saving vocabulary ground truth...")
    with open(output_dir / "scenario_vocabulary.json", 'w', encoding='utf-8') as f:
        json.dump(SCENARIO_VOCABULARY, f, ensure_ascii=False, indent=2)

    # 5. Create CEFR rubrics
    print("\n5. Saving CEFR rubrics...")
    with open(output_dir / "cefr_rubrics.json", 'w', encoding='utf-8') as f:
        json.dump(CEFR_RUBRICS, f, ensure_ascii=False, indent=2)

    # Summary
    print("\n" + "=" * 60)
    print("EVALUATION FILES CREATED")
    print("=" * 60)
    print(f"\nOutput directory: {output_dir}")
    print("\nFiles:")
    print("  📊 model_eval_ground_truth.json  - For testing fine-tuned model")
    print("  📝 crowdsourcing_task.csv        - Template for Prolific/MTurk")
    print("  📋 user_assessment_rubrics.json  - For scoring learner responses")
    print("  📚 scenario_vocabulary.json      - Expected words per scenario/level")
    print("  🎯 cefr_rubrics.json             - CEFR proficiency criteria")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
