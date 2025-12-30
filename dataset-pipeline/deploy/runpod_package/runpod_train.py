#!/usr/bin/env python3
"""
RunPod Training Script for Catalan-Spanish Model

Optimized for A100 GPUs with faster training settings.

Usage on RunPod:
    # Quick training (1 epoch, ~30 min)
    python deploy/runpod_train.py --quick

    # Full training (3 epochs, ~2 hours)
    python deploy/runpod_train.py --full

    # Custom settings
    python deploy/runpod_train.py --epochs 5 --batch-size 8 --lora-r 64
"""

import argparse
import json
import torch
import os
from pathlib import Path
from datetime import datetime


def get_gpu_info():
    """Print GPU information."""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"GPU: {gpu_name}")
        print(f"Memory: {gpu_mem:.1f} GB")
        return gpu_name, gpu_mem
    else:
        print("No CUDA GPU available!")
        return None, 0


def train_model(
    model_name: str = "meta-llama/Llama-3.2-1B-Instruct",
    train_file: str = "data/processed/train_catalan_spanish.jsonl",
    eval_file: str = "data/processed/eval_catalan_spanish.jsonl",
    output_dir: str = "models/catalan-spanish-runpod",
    num_epochs: int = 3,
    batch_size: int = 4,
    gradient_accumulation: int = 4,
    learning_rate: float = 2e-4,
    lora_r: int = 64,
    lora_alpha: int = 16,
    max_length: int = 512,
    use_flash_attention: bool = True,
    use_4bit: bool = False,
):
    """
    Train the model with A100-optimized settings.
    """
    from datasets import load_dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
        DataCollatorForSeq2Seq,
        BitsAndBytesConfig,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    print("=" * 60)
    print("CATALAN-SPANISH MODEL TRAINING (RunPod A100)")
    print("=" * 60)

    # GPU info
    gpu_name, gpu_mem = get_gpu_info()

    # Adjust settings based on GPU memory
    if gpu_mem >= 80:  # A100 80GB
        batch_size = max(batch_size, 8)
        gradient_accumulation = 2
    elif gpu_mem >= 40:  # A100 40GB
        batch_size = max(batch_size, 4)
        gradient_accumulation = 4

    print(f"\nTraining Configuration:")
    print(f"  Model: {model_name}")
    print(f"  Epochs: {num_epochs}")
    print(f"  Batch size: {batch_size}")
    print(f"  Gradient accumulation: {gradient_accumulation}")
    print(f"  Effective batch size: {batch_size * gradient_accumulation}")
    print(f"  LoRA rank: {lora_r}")
    print(f"  Learning rate: {learning_rate}")
    print("=" * 60)

    # Load tokenizer
    print("\n1. Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model
    print("\n2. Loading model...")
    model_kwargs = {
        "torch_dtype": torch.bfloat16,  # Better for A100
        "device_map": "auto",
        "trust_remote_code": True,
    }

    if use_flash_attention:
        model_kwargs["attn_implementation"] = "flash_attention_2"
        print("   Using Flash Attention 2")

    if use_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        model_kwargs["quantization_config"] = bnb_config
        print("   Using 4-bit quantization")

    model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)

    if use_4bit:
        model = prepare_model_for_kbit_training(model)

    # Configure LoRA
    print("\n3. Configuring LoRA...")
    lora_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.enable_input_require_grads()
    model.print_trainable_parameters()

    # Load datasets
    print("\n4. Loading datasets...")
    dataset = load_dataset(
        "json",
        data_files={"train": train_file, "eval": eval_file},
    )
    print(f"   Train: {len(dataset['train'])} examples")
    print(f"   Eval: {len(dataset['eval'])} examples")

    # Format and tokenize
    def format_chat(example):
        messages = example.get("messages", [])
        if hasattr(tokenizer, "apply_chat_template"):
            text = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False
            )
        else:
            text = ""
            for msg in messages:
                text += f"<|{msg['role']}|>\n{msg['content']}\n"
        return {"text": text}

    def tokenize(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_length,
            padding="max_length",
        )

    print("\n5. Processing datasets...")
    dataset = dataset.map(format_chat, remove_columns=dataset["train"].column_names)
    dataset = dataset.map(tokenize, batched=True, remove_columns=["text"])

    def add_labels(examples):
        examples["labels"] = examples["input_ids"].copy()
        return examples

    dataset = dataset.map(add_labels, batched=True)

    # Training arguments (optimized for A100)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        bf16=True,  # Use bf16 on A100
        tf32=True,  # Enable TF32 for faster matmuls
        gradient_checkpointing=True,
        optim="adamw_torch_fused",  # Faster optimizer
        report_to="none",
        dataloader_num_workers=4,
        dataloader_pin_memory=True,
    )

    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        return_tensors="pt",
    )

    # Trainer
    print("\n6. Starting training...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["eval"],
        data_collator=data_collator,
    )

    # Train
    start_time = datetime.now()
    trainer.train()
    training_time = datetime.now() - start_time

    # Save
    print("\n7. Saving model...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Save config
    config = {
        "base_model": model_name,
        "lora_r": lora_r,
        "lora_alpha": lora_alpha,
        "num_epochs": num_epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "training_time": str(training_time),
        "gpu": gpu_name,
        "train_examples": len(dataset["train"]),
        "eval_examples": len(dataset["eval"]),
    }
    with open(output_path / "training_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print(f"Time: {training_time}")
    print(f"Model saved to: {output_dir}")
    print("\nTo download your model:")
    print(f"  runpodctl send {output_dir}")
    print("\nOr upload to HuggingFace:")
    print(f"  huggingface-cli upload your-username/catalan-spanish {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Train Catalan-Spanish model on RunPod")

    # Presets
    parser.add_argument("--quick", action="store_true", help="Quick training (1 epoch)")
    parser.add_argument("--full", action="store_true", help="Full training (3 epochs)")

    # Custom settings
    parser.add_argument("--model", default="meta-llama/Llama-3.2-1B-Instruct")
    parser.add_argument("--train-file", default="data/processed/train_catalan_spanish.jsonl")
    parser.add_argument("--eval-file", default="data/processed/eval_catalan_spanish.jsonl")
    parser.add_argument("--output", default="models/catalan-spanish-runpod")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lora-r", type=int, default=64)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--use-4bit", action="store_true")
    parser.add_argument("--no-flash-attention", action="store_true")

    args = parser.parse_args()

    # Apply presets
    if args.quick:
        args.epochs = 1
        args.batch_size = 8
    elif args.full:
        args.epochs = 3
        args.batch_size = 4
        args.lora_r = 64

    train_model(
        model_name=args.model,
        train_file=args.train_file,
        eval_file=args.eval_file,
        output_dir=args.output,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        lora_r=args.lora_r,
        learning_rate=args.lr,
        use_4bit=args.use_4bit,
        use_flash_attention=not args.no_flash_attention,
    )


if __name__ == "__main__":
    main()
