#!/usr/bin/env python3
"""
Tokenizer Expansion for Catalan-Accented Spanish

This script:
1. Adds Catalan-specific tokens to the tokenizer
2. Resizes model embeddings and lm_head
3. Saves the expanded tokenizer and model for continued pre-training

Based on research from:
- LLaMa2lang methodology
- Llama 3 multilingual fine-tuning best practices
"""

import argparse
import json
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict


# Catalan-specific vocabulary to add
# These are regional expressions used in Catalan-accented Spanish
CATALAN_TOKENS = {
    # Common interjections and fillers
    "interjections": [
        "ostras",      # Catalan expression of surprise
        "home",        # Catalan filler (like "man" or "dude")
        "apa",         # Catalan interjection
        "collons",     # Catalan expletive (mild)
        "nen",         # "boy" in Catalan
        "nena",        # "girl" in Catalan
        "bueno",       # Common but with Catalan intonation patterns
    ],

    # Family terms (Catalan influence)
    "family": [
        "avi",         # grandfather in Catalan
        "àvia",        # grandmother in Catalan
        "iaia",        # grandma (informal)
        "iaio",        # grandpa (informal)
    ],

    # Common Catalan-Spanish code-switching phrases
    "phrases": [
        "va",          # "come on" / "let's go"
        "apa va",      # "come on then"
        "fem",         # "let's do it"
        "escolta",     # "listen" (Catalan)
        "mira",        # common in both but with Catalan usage patterns
        "clar",        # "of course" in Catalan
        "si us plau",  # "please" in Catalan
        "adéu",        # "goodbye" in Catalan
    ],

    # Regional expressions
    "expressions": [
        "flipar",      # to be amazed (regional slang)
        "molar",       # to be cool (regional slang)
        "rallat",      # stressed/upset (Catalan slang)
        "petar",       # to break/explode (Catalan slang)
        "ximo",        # from Catalan "xim-xim" (tipsy)
    ],

    # Place-related
    "places": [
        "barri",       # neighborhood (Catalan)
        "plaça",       # plaza/square (Catalan spelling)
        "carrer",      # street (Catalan)
        "rambla",      # famous Barcelona street type
    ],
}


def get_all_catalan_tokens() -> List[str]:
    """Flatten all Catalan tokens into a single list."""
    tokens = []
    for category, words in CATALAN_TOKENS.items():
        tokens.extend(words)
    return tokens


def check_token_coverage(tokenizer, tokens: List[str]) -> Dict:
    """
    Check how the current tokenizer handles Catalan tokens.
    Returns statistics about single-token vs multi-token encoding.
    """
    results = {
        "single_token": [],
        "multi_token": [],
        "token_counts": {}
    }

    for word in tokens:
        encoded = tokenizer.encode(word, add_special_tokens=False)
        results["token_counts"][word] = len(encoded)

        if len(encoded) == 1:
            results["single_token"].append(word)
        else:
            results["multi_token"].append({
                "word": word,
                "tokens": len(encoded),
                "decoded": [tokenizer.decode([t]) for t in encoded]
            })

    return results


def expand_tokenizer(
    tokenizer,
    new_tokens: List[str],
    verbose: bool = True
) -> int:
    """
    Add new tokens to the tokenizer.
    Returns the number of tokens actually added.
    """
    # Filter to only tokens that aren't already single tokens
    tokens_to_add = []

    for token in new_tokens:
        encoded = tokenizer.encode(token, add_special_tokens=False)
        if len(encoded) > 1:  # Only add if currently multi-token
            tokens_to_add.append(token)
            if verbose:
                print(f"  Adding: '{token}' (was {len(encoded)} tokens)")
        elif verbose:
            print(f"  Skipping: '{token}' (already single token)")

    if tokens_to_add:
        num_added = tokenizer.add_tokens(tokens_to_add)
        return num_added

    return 0


def resize_model_embeddings(model, tokenizer, verbose: bool = True):
    """
    Resize model embeddings to match expanded tokenizer.
    Initializes new embeddings with mean of existing embeddings.
    """
    old_vocab_size = model.config.vocab_size
    new_vocab_size = len(tokenizer)

    if new_vocab_size == old_vocab_size:
        if verbose:
            print("No resizing needed - vocabulary size unchanged")
        return

    if verbose:
        print(f"Resizing embeddings: {old_vocab_size} -> {new_vocab_size}")

    # Resize token embeddings
    model.resize_token_embeddings(new_vocab_size)

    # Initialize new embeddings with mean of existing embeddings
    # This helps the model learn faster for new tokens
    with torch.no_grad():
        # Get embedding layer
        if hasattr(model, 'model'):
            embed_tokens = model.model.embed_tokens
        else:
            embed_tokens = model.get_input_embeddings()

        # Calculate mean of existing embeddings
        existing_embeddings = embed_tokens.weight[:old_vocab_size]
        mean_embedding = existing_embeddings.mean(dim=0)

        # Initialize new embeddings with mean
        for i in range(old_vocab_size, new_vocab_size):
            embed_tokens.weight[i] = mean_embedding

    if verbose:
        print(f"  Initialized {new_vocab_size - old_vocab_size} new embeddings with mean")


def main():
    parser = argparse.ArgumentParser(
        description="Expand tokenizer with Catalan-specific tokens"
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="meta-llama/Llama-3.2-1B",
        help="Base model to expand",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="models/catalan-spanish-expanded",
        help="Output directory for expanded model",
    )
    parser.add_argument(
        "--custom_tokens_file",
        type=str,
        default=None,
        help="Optional JSON file with additional custom tokens",
    )
    parser.add_argument(
        "--check_only",
        action="store_true",
        help="Only check token coverage, don't modify",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("TOKENIZER EXPANSION FOR CATALAN-SPANISH")
    print("=" * 60)
    print(f"Base model: {args.model_name}")
    print(f"Output: {args.output_dir}")
    print("=" * 60)

    # Load tokenizer
    print("\n1. Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    print(f"   Original vocabulary size: {len(tokenizer)}")

    # Get tokens to add
    catalan_tokens = get_all_catalan_tokens()
    print(f"\n2. Catalan tokens to consider: {len(catalan_tokens)}")

    # Load custom tokens if provided
    if args.custom_tokens_file:
        with open(args.custom_tokens_file, 'r', encoding='utf-8') as f:
            custom = json.load(f)
            if isinstance(custom, list):
                catalan_tokens.extend(custom)
            elif isinstance(custom, dict):
                for tokens in custom.values():
                    catalan_tokens.extend(tokens)
        print(f"   Added custom tokens, total: {len(catalan_tokens)}")

    # Check current coverage
    print("\n3. Checking current token coverage...")
    coverage = check_token_coverage(tokenizer, catalan_tokens)
    print(f"   Already single-token: {len(coverage['single_token'])}")
    print(f"   Multi-token (need adding): {len(coverage['multi_token'])}")

    if coverage['multi_token']:
        print("\n   Multi-token words:")
        for item in coverage['multi_token'][:10]:  # Show first 10
            print(f"     '{item['word']}' -> {item['tokens']} tokens: {item['decoded']}")
        if len(coverage['multi_token']) > 10:
            print(f"     ... and {len(coverage['multi_token']) - 10} more")

    if args.check_only:
        print("\n[Check only mode - not modifying tokenizer]")
        return

    # Expand tokenizer
    print("\n4. Expanding tokenizer...")
    num_added = expand_tokenizer(tokenizer, catalan_tokens)
    print(f"   Added {num_added} new tokens")
    print(f"   New vocabulary size: {len(tokenizer)}")

    if num_added == 0:
        print("\nNo new tokens needed - tokenizer already has good coverage!")
        print("You can proceed directly to fine-tuning with the original model.")
        return

    # Load model and resize embeddings
    print("\n5. Loading model and resizing embeddings...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )

    resize_model_embeddings(model, tokenizer)

    # Save expanded model and tokenizer
    print("\n6. Saving expanded model and tokenizer...")
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    tokenizer.save_pretrained(output_path)
    model.save_pretrained(output_path)

    # Save token expansion info
    expansion_info = {
        "base_model": args.model_name,
        "original_vocab_size": model.config.vocab_size - num_added,
        "new_vocab_size": len(tokenizer),
        "tokens_added": num_added,
        "catalan_tokens": catalan_tokens,
        "coverage_before": {
            "single_token": coverage['single_token'],
            "multi_token": [m['word'] for m in coverage['multi_token']]
        }
    }
    with open(output_path / "expansion_info.json", 'w', encoding='utf-8') as f:
        json.dump(expansion_info, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("TOKENIZER EXPANSION COMPLETE!")
    print("=" * 60)
    print(f"\nExpanded model saved to: {args.output_dir}")
    print("\nNext steps:")
    print("  1. Continue pre-training on Catalan text (optional but recommended)")
    print("     python src/pretrain_catalan.py --model_path", args.output_dir)
    print("  2. Fine-tune with LoRA on conversation data")
    print("     python src/finetune.py --model_name", args.output_dir)


if __name__ == "__main__":
    main()
