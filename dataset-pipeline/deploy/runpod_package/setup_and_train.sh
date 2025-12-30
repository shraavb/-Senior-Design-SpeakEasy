#!/bin/bash
# RunPod One-Liner Setup & Training Script
#
# Usage: Just copy-paste this entire script into RunPod terminal
#
# Or run: curl -sSL https://raw.githubusercontent.com/shraavb/-Senior-Design-SpeakEasy/main/dataset-pipeline/deploy/runpod_package/setup_and_train.sh | bash

set -e

echo "=============================================="
echo "🚀 CATALAN-SPANISH MODEL - RUNPOD SETUP"
echo "=============================================="

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q torch transformers accelerate peft datasets bitsandbytes
pip install -q huggingface_hub tqdm rich

# Create directories
mkdir -p /workspace/catalan-spanish/data/processed
mkdir -p /workspace/catalan-spanish/models
cd /workspace/catalan-spanish

# Download training script
echo "📥 Downloading training script..."
cat > train.py << 'TRAINSCRIPT'
#!/usr/bin/env python3
import argparse
import json
import torch
from pathlib import Path
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, TrainingArguments,
    Trainer, DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="meta-llama/Llama-3.2-1B-Instruct")
    parser.add_argument("--train-file", default="data/processed/train_catalan_spanish.jsonl")
    parser.add_argument("--eval-file", default="data/processed/eval_catalan_spanish.jsonl")
    parser.add_argument("--output", default="models/catalan-spanish-finetuned")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lora-r", type=int, default=64)
    args = parser.parse_args()

    print("=" * 60)
    print("TRAINING CATALAN-SPANISH MODEL")
    print("=" * 60)
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Model: {args.model}")
    print(f"Epochs: {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print("=" * 60)

    # Load tokenizer & model
    print("\n1. Loading model...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="flash_attention_2",
    )

    # LoRA
    print("\n2. Configuring LoRA...")
    lora_config = LoraConfig(
        r=args.lora_r, lora_alpha=16,
        target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
        lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.enable_input_require_grads()
    model.print_trainable_parameters()

    # Load data
    print("\n3. Loading data...")
    dataset = load_dataset("json", data_files={"train": args.train_file, "eval": args.eval_file})
    print(f"   Train: {len(dataset['train'])}, Eval: {len(dataset['eval'])}")

    def process(example):
        msgs = example.get("messages", [])
        text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
        tokens = tokenizer(text, truncation=True, max_length=512, padding="max_length")
        tokens["labels"] = tokens["input_ids"].copy()
        return tokens

    dataset = dataset.map(process, remove_columns=dataset["train"].column_names)

    # Train
    print("\n4. Training...")
    Path(args.output).mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=args.output,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="epoch",
        bf16=True,
        tf32=True,
        gradient_checkpointing=True,
        optim="adamw_torch_fused",
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["eval"],
        data_collator=DataCollatorForSeq2Seq(tokenizer, model, padding=True),
    )
    trainer.train()

    # Save
    print("\n5. Saving...")
    trainer.save_model(args.output)
    tokenizer.save_pretrained(args.output)

    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE!")
    print("=" * 60)
    print(f"Model saved to: {args.output}")

if __name__ == "__main__":
    main()
TRAINSCRIPT

echo ""
echo "=============================================="
echo "✅ SETUP COMPLETE!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Upload your training data:"
echo "   (From your LOCAL machine run:)"
echo "   runpodctl send train_catalan_spanish.jsonl"
echo "   runpodctl send eval_catalan_spanish.jsonl"
echo ""
echo "2. Move data to correct location:"
echo "   mv /workspace/train_catalan_spanish.jsonl data/processed/"
echo "   mv /workspace/eval_catalan_spanish.jsonl data/processed/"
echo ""
echo "3. Login to HuggingFace (for Llama access):"
echo "   huggingface-cli login"
echo ""
echo "4. Start training:"
echo "   python train.py --epochs 3"
echo ""
echo "5. Download your model (from LOCAL machine):"
echo "   runpodctl receive models/catalan-spanish-finetuned"
echo ""
