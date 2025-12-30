#!/usr/bin/env python3
"""
Continued Pre-training for Catalan-Spanish Model

This script performs continued pre-training on Catalan text to:
1. Train the new token embeddings (after tokenizer expansion)
2. Improve the model's understanding of Catalan vocabulary and patterns

Use this after running tokenizer_expansion.py and before finetune.py
"""

import argparse
import json
import os
import torch
from pathlib import Path
from datasets import load_dataset, Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model


def load_text_corpus(corpus_path: str) -> Dataset:
    """
    Load text corpus from a directory of .txt files or a single file.
    """
    texts = []

    path = Path(corpus_path)

    if path.is_file():
        # Single file
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Split into chunks (roughly paragraph-sized)
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            texts.extend(paragraphs)
    elif path.is_dir():
        # Directory of files
        for txt_file in path.glob('*.txt'):
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                texts.extend(paragraphs)
    else:
        raise ValueError(f"Corpus path not found: {corpus_path}")

    print(f"Loaded {len(texts)} text segments from corpus")

    return Dataset.from_dict({"text": texts})


def create_sample_corpus(output_path: str):
    """
    Create a sample Catalan-Spanish corpus for testing.
    In production, replace with actual Catalan text data.
    """
    sample_texts = [
        # Catalan-influenced Spanish examples
        "Ostras, nen, qué sorpresa verte por aquí. ¿Cómo va todo?",
        "Home, no me digas eso. Ya sabes que siempre estoy aquí para ayudarte.",
        "Apa, vamos a tomar algo en el barri. Conozco un bar genial en la rambla.",
        "Escolta, tengo que contarte algo muy importante sobre el trabajo.",
        "La nena se ha ido a casa de los avis para pasar el fin de semana.",
        "¿Qué, quedamos mañana? Va, no seas rallat y ven con nosotros.",
        "Clar que sí, home. Siempre puedes contar conmigo.",
        "Me flipa este restaurante. La comida está que mola.",
        "Fem una cosa: primero vamos al mercado y después a la plaça.",
        "Adéu, nena. Nos vemos el próximo fin de semana en Barcelona.",
        # More conversational examples
        "Bienvenidos a Barcelona. Esta ciudad es increíble, ya veréis.",
        "¿Te gustaría venir a oír una guitarra maravillosa esta noche?",
        "No podemos. Tenemos planes para mañana.",
        "Es genial. Estoy feliz por ti, de verdad.",
        "¿Cómo estás? Dios mío, ¿qué haces aquí tan temprano?",
        "Hola, cariño. ¿Te desperté? Perdona por llamar tan tarde.",
        "Pues cuando salga de la reunión, ¿puedes decirle que me llame?",
        "Buenos días, tengo una cita con el señor García a las diez.",
        "¡Hasta luego! Ha sido un placer conocerte.",
        "Perdón, disculpa. No era mi intención molestarte.",
        # Extended corpus for better pre-training
        "Buenas tardes, ¿qué tal el día? Espero que todo vaya bien por tu casa.",
        "Sí, sí, tranquilo. No pasa nada, ya lo arreglaremos mañana.",
        "Mira, nen, te lo digo en serio: esto es muy importante para todos.",
        "Vale, pues entonces quedamos a las ocho en la plaça del barri.",
        "¿Has visto a la Maria? Hace días que no la veo por aquí.",
        "Claro que sí, faltaría más. Cuenta conmigo para lo que necesites.",
        "Escucha, tengo que contarte algo que me ha pasado hoy en el trabajo.",
        "No te preocupes, home. Todo saldrá bien, ya lo verás.",
        "¿Qué te parece si vamos a cenar a ese restaurante nuevo del centro?",
        "Uf, qué calor hace hoy. ¿Vamos a tomar algo fresquito?",
        "La familia está bien, gracias por preguntar. Los avis están contentísimos.",
        "Oye, ¿has probado las tapas de ese bar de la esquina? Están buenísimas.",
        "Venga, va, no te hagas de rogar. Ven con nosotros que lo pasaremos bien.",
        "Me alegro mucho de verte. Hacía tiempo que no quedábamos, ¿eh?",
        "Pues nada, eso es todo. Ya te contaré cómo ha ido la reunión.",
        "Buf, menudo día llevo. Estoy agotado de tanto trabajar.",
        "¿Te acuerdas de cuando íbamos juntos al colegio? Qué tiempos aquellos.",
        "Sí, sí, ya sé lo que me quieres decir. No hace falta que me lo repitas.",
        "Madre mía, qué tarde es ya. Tengo que irme corriendo a casa.",
        "Oye, ¿sabes algo de lo que pasó ayer en la reunión de vecinos?",
    ]

    path = Path(output_path)
    path.mkdir(parents=True, exist_ok=True)

    with open(path / "sample_corpus.txt", 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(sample_texts))

    print(f"Created sample corpus at: {path / 'sample_corpus.txt'}")
    print("Note: For production, replace with larger Catalan text corpus")

    return str(path)


def tokenize_for_pretraining(examples, tokenizer, max_length, stride):
    """
    Tokenize text for language modeling with sliding window.
    """
    # Concatenate all texts
    concatenated = tokenizer(
        examples["text"],
        truncation=False,
        padding=False,
        return_attention_mask=False,
    )

    # Flatten all input_ids
    all_input_ids = []
    for ids in concatenated["input_ids"]:
        all_input_ids.extend(ids)

    # Create chunks with stride (allow shorter final chunk)
    chunks = []
    min_chunk_size = max_length // 4  # Allow chunks at least 25% of max_length
    for i in range(0, len(all_input_ids), stride):
        chunk = all_input_ids[i:i + max_length]
        if len(chunk) >= min_chunk_size:
            # Pad shorter chunks
            if len(chunk) < max_length:
                chunk = chunk + [0] * (max_length - len(chunk))
            chunks.append(chunk)

    return {"input_ids": chunks}


def main():
    parser = argparse.ArgumentParser(
        description="Continue pre-training on Catalan text"
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default="models/catalan-spanish-expanded",
        help="Path to expanded model (from tokenizer_expansion.py)",
    )
    parser.add_argument(
        "--corpus_path",
        type=str,
        default=None,
        help="Path to Catalan text corpus (directory or file)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="models/catalan-spanish-pretrained",
        help="Output directory for pre-trained model",
    )
    parser.add_argument(
        "--max_length",
        type=int,
        default=512,
        help="Maximum sequence length",
    )
    parser.add_argument(
        "--num_epochs",
        type=int,
        default=2,
        help="Number of pre-training epochs",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=4,
        help="Training batch size",
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=1e-4,
        help="Learning rate (lower than fine-tuning)",
    )
    parser.add_argument(
        "--use_lora",
        action="store_true",
        help="Use LoRA for pre-training (saves memory but may be less effective for new tokens)",
    )
    parser.add_argument(
        "--create_sample",
        action="store_true",
        help="Create a sample corpus for testing",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("CONTINUED PRE-TRAINING FOR CATALAN-SPANISH")
    print("=" * 60)
    print(f"Model: {args.model_path}")
    print(f"Output: {args.output_dir}")
    print(f"Use LoRA: {args.use_lora}")
    print("=" * 60)

    # Create sample corpus if requested
    if args.create_sample:
        corpus_path = create_sample_corpus("data/catalan_corpus")
        if not args.corpus_path:
            args.corpus_path = corpus_path

    if not args.corpus_path:
        print("\nError: No corpus path provided.")
        print("Either provide --corpus_path or use --create_sample")
        return

    # Check for device
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"\nUsing device: {device}")

    # Load tokenizer and model
    print("\n1. Loading model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.float16 if device != "cpu" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
    )

    if device == "mps":
        model = model.to(device)

    print(f"   Vocabulary size: {len(tokenizer)}")

    # Apply LoRA if requested
    if args.use_lora:
        print("\n2. Configuring LoRA...")
        lora_config = LoraConfig(
            r=64,
            lora_alpha=16,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora_config)
        model.enable_input_require_grads()
        model.print_trainable_parameters()

    # Load corpus
    print(f"\n3. Loading corpus from: {args.corpus_path}")
    dataset = load_text_corpus(args.corpus_path)

    # Tokenize
    print("\n4. Tokenizing corpus...")
    stride = args.max_length // 2  # 50% overlap

    tokenized = dataset.map(
        lambda x: tokenize_for_pretraining(x, tokenizer, args.max_length, stride),
        batched=True,
        remove_columns=["text"],
    )

    # Flatten the chunked data
    all_chunks = []
    for item in tokenized:
        if isinstance(item["input_ids"][0], list):
            all_chunks.extend(item["input_ids"])
        else:
            all_chunks.append(item["input_ids"])

    train_dataset = Dataset.from_dict({"input_ids": all_chunks})
    print(f"   Created {len(train_dataset)} training sequences")

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.num_epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        learning_rate=args.learning_rate,
        weight_decay=0.01,
        warmup_ratio=0.1,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        fp16=device == "cuda",
        bf16=False,
        gradient_checkpointing=device == "cuda",
        report_to="none",
    )

    # Data collator for language modeling
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # Causal LM, not masked LM
    )

    # Initialize trainer
    print("\n5. Starting pre-training...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator,
    )

    # Train
    print("\n" + "=" * 60)
    print("PRE-TRAINING IN PROGRESS")
    print("=" * 60 + "\n")

    trainer.train()

    # Save
    print("\n6. Saving pre-trained model...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    # Save config
    config = {
        "base_model": args.model_path,
        "corpus_path": args.corpus_path,
        "num_epochs": args.num_epochs,
        "learning_rate": args.learning_rate,
        "max_length": args.max_length,
        "used_lora": args.use_lora,
        "train_sequences": len(train_dataset),
    }
    with open(output_path / "pretrain_config.json", 'w') as f:
        json.dump(config, f, indent=2)

    print("\n" + "=" * 60)
    print("PRE-TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\nModel saved to: {args.output_dir}")
    print("\nNext step: Fine-tune with LoRA")
    print(f"  python src/finetune.py --model_name {args.output_dir}")


if __name__ == "__main__":
    main()
