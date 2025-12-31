#!/usr/bin/env python3
"""
Convert synthetic slang examples to JSONL training format.
Combines Catalan and Spanish slang examples into fine-tuning data.
"""

import json
from pathlib import Path

def load_synthetic_examples(filepath):
    """Load synthetic examples from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('examples', [])

def create_training_example(example, slang_type):
    """Convert a synthetic example to training format."""
    scenario = example.get('scenario', 'general')
    text = example.get('text', '')
    slang_terms = example.get('slang_terms', [])
    context = example.get('context', '')

    # Create system prompt based on slang type
    if slang_type == 'catalan':
        system_prompt = (
            "You are a native Spanish speaker from Barcelona, Catalonia. "
            "You speak Spanish with Catalan influence and naturally use Catalan slang expressions. "
            "Your speech is informal, friendly, and typical of young Barcelona locals."
        )
    else:
        system_prompt = (
            "You are a native Spanish speaker from Spain. "
            "You speak informal, colloquial Spanish and naturally use common Spanish slang expressions. "
            "Your speech is casual and typical of young Spanish speakers."
        )

    # Create user prompt based on scenario
    scenario_prompts = {
        'greetings': "Say hello to a friend you haven't seen in a while.",
        'reactions': "React to something surprising or amazing.",
        'plans': "Suggest making plans with a friend.",
        'emotions': "Express how you're feeling right now.",
        'opinions': "Share your opinion on something.",
        'party': "Talk about going out or a party.",
        'money': "Discuss money or being broke.",
        'work': "Talk about work.",
        'fillers': "End a conversation naturally.",
        'small_talk': "Make casual conversation.",
        'farewells': "Say goodbye to a friend.",
        'requests': "Ask someone for help.",
        'apologies': "Apologize for something.",
        'family': "Talk about family.",
    }

    user_prompt = scenario_prompts.get(scenario, f"Have a casual conversation about {scenario}.")
    if context:
        user_prompt = f"{user_prompt} Context: {context}"

    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": text}
        ],
        "metadata": {
            "scenario": scenario,
            "slang_type": slang_type,
            "slang_terms": slang_terms,
            "source": "synthetic"
        }
    }

def main():
    data_dir = Path(__file__).parent / "data" / "processed"
    output_dir = data_dir / "slang_filtered"
    output_dir.mkdir(exist_ok=True)

    # Load synthetic examples
    catalan_file = data_dir / "synthetic_catalan_slang.json"
    spanish_file = data_dir / "synthetic_spanish_slang.json"

    all_examples = []

    if catalan_file.exists():
        catalan_examples = load_synthetic_examples(catalan_file)
        for ex in catalan_examples:
            all_examples.append(create_training_example(ex, 'catalan'))
        print(f"Loaded {len(catalan_examples)} Catalan slang examples")

    if spanish_file.exists():
        spanish_examples = load_synthetic_examples(spanish_file)
        for ex in spanish_examples:
            all_examples.append(create_training_example(ex, 'spanish'))
        print(f"Loaded {len(spanish_examples)} Spanish slang examples")

    # Write to JSONL
    output_file = output_dir / "synthetic_slang_training.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"\nWrote {len(all_examples)} training examples to {output_file}")

    # Also create a combined file with original + synthetic data
    original_train = data_dir / "train_catalan_spanish.jsonl"
    if original_train.exists():
        combined_file = output_dir / "train_with_slang_augmented.jsonl"

        # Copy original and add synthetic
        with open(combined_file, 'w', encoding='utf-8') as out:
            # Add original training data
            with open(original_train, 'r', encoding='utf-8') as f:
                original_count = 0
                for line in f:
                    out.write(line)
                    original_count += 1

            # Add synthetic examples
            for example in all_examples:
                out.write(json.dumps(example, ensure_ascii=False) + '\n')

        print(f"Created combined training file with {original_count} original + {len(all_examples)} synthetic = {original_count + len(all_examples)} total examples")
        print(f"Output: {combined_file}")

if __name__ == "__main__":
    main()
