#!/usr/bin/env python3
"""
Full Training Pipeline for Catalan-Spanish Model

This script provides a unified interface to run either:
- Approach 1: LoRA fine-tuning only (simple, fast)
- Approach 2: Tokenizer expansion + pre-training + LoRA (comprehensive)

Usage:
    # Approach 1: Quick LoRA fine-tuning
    python src/train_catalan_model.py --approach 1

    # Approach 2: Full pipeline with tokenizer expansion
    python src/train_catalan_model.py --approach 2

    # Compare both approaches
    python src/train_catalan_model.py --compare
"""

import argparse
import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime


def run_command(cmd: list, description: str) -> dict:
    """Run a command and capture timing/output."""
    print(f"\n{'=' * 60}")
    print(f"RUNNING: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('=' * 60 + "\n")

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
        )
        success = True
        error = None
    except subprocess.CalledProcessError as e:
        success = False
        error = str(e)

    elapsed = time.time() - start_time

    return {
        "description": description,
        "command": ' '.join(cmd),
        "success": success,
        "elapsed_seconds": elapsed,
        "elapsed_formatted": f"{int(elapsed // 3600)}h {int((elapsed % 3600) // 60)}m {int(elapsed % 60)}s",
        "error": error,
    }


def approach_1_lora_only(args) -> dict:
    """
    Approach 1: Direct LoRA fine-tuning on conversation data.
    Simple and fast, works well when tokenizer already handles vocabulary.
    """
    print("\n" + "=" * 60)
    print("APPROACH 1: LoRA FINE-TUNING ONLY")
    print("=" * 60)

    results = {
        "approach": 1,
        "name": "LoRA Fine-Tuning Only",
        "start_time": datetime.now().isoformat(),
        "steps": [],
    }

    # Step 1: Fine-tune with LoRA
    cmd = [
        sys.executable, "src/finetune.py",
        "--model_name", args.base_model,
        "--train_file", args.train_file,
        "--eval_file", args.eval_file,
        "--output_dir", "models/approach1-lora-only",
        "--num_epochs", str(args.num_epochs),
        "--lora_r", "64",
        "--lora_alpha", "16",
        "--batch_size", str(args.batch_size),
    ]

    if args.use_4bit:
        cmd.append("--use_4bit")

    step_result = run_command(cmd, "LoRA Fine-tuning")
    results["steps"].append(step_result)

    results["end_time"] = datetime.now().isoformat()
    results["success"] = all(s["success"] for s in results["steps"])
    results["total_time"] = sum(s["elapsed_seconds"] for s in results["steps"])
    results["output_model"] = "models/approach1-lora-only"

    return results


def approach_2_full_pipeline(args) -> dict:
    """
    Approach 2: Tokenizer expansion + pre-training + LoRA fine-tuning.
    More comprehensive, better for deep dialect specialization.
    """
    print("\n" + "=" * 60)
    print("APPROACH 2: TOKENIZER EXPANSION + PRE-TRAINING + LoRA")
    print("=" * 60)

    results = {
        "approach": 2,
        "name": "Tokenizer Expansion + Pre-training + LoRA",
        "start_time": datetime.now().isoformat(),
        "steps": [],
    }

    # Step 1: Expand tokenizer
    cmd = [
        sys.executable, "src/tokenizer_expansion.py",
        "--model_name", args.base_model,
        "--output_dir", "models/approach2-step1-expanded",
    ]
    step_result = run_command(cmd, "Tokenizer Expansion")
    results["steps"].append(step_result)

    if not step_result["success"]:
        results["success"] = False
        return results

    # Step 2: Continue pre-training (with sample corpus if no corpus provided)
    cmd = [
        sys.executable, "src/pretrain_catalan.py",
        "--model_path", "models/approach2-step1-expanded",
        "--output_dir", "models/approach2-step2-pretrained",
        "--num_epochs", "2",
        "--batch_size", str(args.batch_size),
        "--create_sample",  # Create sample corpus for testing
    ]

    if args.corpus_path:
        cmd.extend(["--corpus_path", args.corpus_path])
        cmd.remove("--create_sample")

    if args.use_lora_pretrain:
        cmd.append("--use_lora")

    step_result = run_command(cmd, "Continued Pre-training")
    results["steps"].append(step_result)

    if not step_result["success"]:
        results["success"] = False
        return results

    # Step 3: Fine-tune with LoRA
    cmd = [
        sys.executable, "src/finetune.py",
        "--model_name", "models/approach2-step2-pretrained",
        "--train_file", args.train_file,
        "--eval_file", args.eval_file,
        "--output_dir", "models/approach2-step3-finetuned",
        "--num_epochs", str(args.num_epochs),
        "--lora_r", "64",
        "--lora_alpha", "16",
        "--batch_size", str(args.batch_size),
    ]

    if args.use_4bit:
        cmd.append("--use_4bit")

    step_result = run_command(cmd, "LoRA Fine-tuning")
    results["steps"].append(step_result)

    results["end_time"] = datetime.now().isoformat()
    results["success"] = all(s["success"] for s in results["steps"])
    results["total_time"] = sum(s["elapsed_seconds"] for s in results["steps"])
    results["output_model"] = "models/approach2-step3-finetuned"

    return results


def compare_approaches(args):
    """Run both approaches and compare results."""
    print("\n" + "=" * 60)
    print("COMPARING BOTH APPROACHES")
    print("=" * 60)

    all_results = {
        "comparison_date": datetime.now().isoformat(),
        "base_model": args.base_model,
        "approaches": [],
    }

    # Run Approach 1
    print("\n" + "-" * 60)
    print("Running Approach 1...")
    print("-" * 60)
    results_1 = approach_1_lora_only(args)
    all_results["approaches"].append(results_1)

    # Run Approach 2
    print("\n" + "-" * 60)
    print("Running Approach 2...")
    print("-" * 60)
    results_2 = approach_2_full_pipeline(args)
    all_results["approaches"].append(results_2)

    # Save comparison results
    output_path = Path("models/comparison_results.json")
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)

    for result in all_results["approaches"]:
        total_mins = result["total_time"] / 60
        print(f"\n{result['name']}:")
        print(f"  Success: {result['success']}")
        print(f"  Total Time: {total_mins:.1f} minutes")
        print(f"  Steps: {len(result['steps'])}")
        print(f"  Output: {result.get('output_model', 'N/A')}")

    print(f"\nDetailed results saved to: {output_path}")
    print("\nNext steps:")
    print("  1. Test both models with sample prompts")
    print("  2. Have native speakers evaluate regional authenticity")
    print("  3. Compare eval loss and perplexity")

    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Train Catalan-Spanish model with different approaches"
    )
    parser.add_argument(
        "--approach",
        type=int,
        choices=[1, 2],
        default=1,
        help="Which approach to use (1=LoRA only, 2=Full pipeline)",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run both approaches and compare",
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default="meta-llama/Llama-3.2-1B",
        help="Base model to fine-tune",
    )
    parser.add_argument(
        "--train_file",
        type=str,
        default="data/processed/train_catalan_spanish.jsonl",
        help="Training data file",
    )
    parser.add_argument(
        "--eval_file",
        type=str,
        default="data/processed/eval_catalan_spanish.jsonl",
        help="Evaluation data file",
    )
    parser.add_argument(
        "--corpus_path",
        type=str,
        default=None,
        help="Path to Catalan text corpus (for Approach 2)",
    )
    parser.add_argument(
        "--num_epochs",
        type=int,
        default=3,
        help="Number of fine-tuning epochs",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=4,
        help="Training batch size",
    )
    parser.add_argument(
        "--use_4bit",
        action="store_true",
        help="Use 4-bit quantization",
    )
    parser.add_argument(
        "--use_lora_pretrain",
        action="store_true",
        help="Use LoRA during pre-training (Approach 2)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("CATALAN-SPANISH MODEL TRAINING PIPELINE")
    print("=" * 60)
    print(f"Base Model: {args.base_model}")
    print(f"Training Data: {args.train_file}")
    print(f"Epochs: {args.num_epochs}")
    print("=" * 60)

    if args.compare:
        compare_approaches(args)
    elif args.approach == 1:
        results = approach_1_lora_only(args)
        print(f"\nApproach 1 completed in {results['total_time']/60:.1f} minutes")
        print(f"Model saved to: {results['output_model']}")
    else:
        results = approach_2_full_pipeline(args)
        print(f"\nApproach 2 completed in {results['total_time']/60:.1f} minutes")
        print(f"Model saved to: {results['output_model']}")


if __name__ == "__main__":
    main()
