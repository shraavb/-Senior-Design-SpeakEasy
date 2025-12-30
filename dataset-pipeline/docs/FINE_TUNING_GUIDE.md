# Fine-Tuning Guide: Catalan-Accented Spanish for SpeakEasy

This document outlines two approaches for fine-tuning Llama models to generate Catalan-accented Spanish for the SpeakEasy language learning app.

---

## Overview

| Approach | Complexity | Training Time | Best For |
|----------|------------|---------------|----------|
| **Approach 1: LoRA Only** | Simple | ~2-4 hours | Quick adaptation, conversational style |
| **Approach 2: Tokenizer Expansion + Pre-training + LoRA** | Advanced | ~8-24 hours | Deep dialect specialization |

---

## Approach 1: LoRA Fine-Tuning Only

### When to Use
- Llama 3's 128K tokenizer already handles Spanish/Catalan vocabulary well
- You want conversational adaptation without deep vocabulary changes
- Limited compute resources or time
- Your dataset already contains the regional expressions you want

### How It Works
LoRA (Low-Rank Adaptation) adds small trainable matrices to the model's attention layers, allowing efficient fine-tuning without modifying all parameters.

**Key Parameters:**
- `lora_r=64` - Rank of the low-rank matrices (higher = more capacity)
- `lora_alpha=16` - Scaling factor
- Trainable parameters: ~3% of model

### Steps

```bash
cd dataset-pipeline

# 1. Ensure you have training data
python src/main.py status

# 2. Run fine-tuning
python src/finetune.py \
    --model_name meta-llama/Llama-3.2-1B \
    --train_file data/processed/train_catalan_spanish.jsonl \
    --eval_file data/processed/eval_catalan_spanish.jsonl \
    --output_dir models/catalan-spanish-lora \
    --num_epochs 3 \
    --lora_r 64 \
    --lora_alpha 16 \
    --batch_size 4
```

### Expected Results
- Model learns Catalan expressions and conversational patterns
- Maintains base model's general Spanish fluency
- Quick training on consumer hardware

### Evaluation Metrics to Track
- Eval loss (should decrease)
- Perplexity on held-out Catalan-Spanish text
- Human evaluation of regional expression usage

---

## Approach 2: Tokenizer Expansion + Pre-training + LoRA

### When to Use
- Llama struggles with Catalan-specific vocabulary
- You want maximum dialect authenticity
- You have access to significant Catalan text for pre-training
- Building a production-grade dialect model

### How It Works

**Step 1: Tokenizer Expansion**
Add Catalan-specific tokens so they're encoded as single tokens instead of being split:

| Word | Before (tokens) | After (tokens) |
|------|-----------------|----------------|
| "ostras" | ["ost", "ras"] (2) | ["ostras"] (1) |
| "nen" | ["n", "en"] (2) | ["nen"] (1) |

**Step 2: Embedding Resize**
Resize model embeddings and lm_head to accommodate new tokens. Initialize new embeddings with the mean of existing embeddings.

**Step 3: Continued Pre-training**
Train the model on raw Catalan/Catalan-Spanish text to learn the new token embeddings.

**Step 4: LoRA Fine-tuning**
Fine-tune on conversation data as in Approach 1.

### Steps

```bash
cd dataset-pipeline

# 1. Check current tokenizer coverage
python src/tokenizer_expansion.py \
    --model_name meta-llama/Llama-3.2-1B \
    --check_only

# 2. Expand tokenizer and resize embeddings
python src/tokenizer_expansion.py \
    --model_name meta-llama/Llama-3.2-1B \
    --output_dir models/catalan-spanish-expanded

# 3. Continue pre-training on Catalan text (optional but recommended)
python src/pretrain_catalan.py \
    --model_path models/catalan-spanish-expanded \
    --corpus_path data/catalan_corpus/ \
    --output_dir models/catalan-spanish-pretrained

# 4. Fine-tune with LoRA
python src/finetune.py \
    --model_name models/catalan-spanish-pretrained \
    --train_file data/processed/train_catalan_spanish.jsonl \
    --eval_file data/processed/eval_catalan_spanish.jsonl \
    --output_dir models/catalan-spanish-full \
    --num_epochs 3 \
    --lora_r 64 \
    --lora_alpha 16
```

### Catalan Tokens Added

| Category | Tokens |
|----------|--------|
| Interjections | ostras, home, apa, collons, nen, nena |
| Family | avi, àvia, iaia, iaio |
| Phrases | va, apa va, fem, escolta, clar, si us plau, adéu |
| Expressions | flipar, molar, rallat |
| Places | barri, plaça, carrer, rambla |

### Expected Results
- Better handling of Catalan-specific vocabulary
- More natural code-switching between Catalan and Spanish
- Higher quality for regional expressions

### Evaluation Metrics to Track
- Token efficiency (fewer tokens for Catalan words)
- Eval loss on pre-training and fine-tuning
- Regional vocabulary usage accuracy
- Human evaluation by native speakers

---

## Comparison Framework

### Quantitative Metrics

| Metric | Approach 1 | Approach 2 |
|--------|------------|------------|
| Training time | | |
| Final eval loss | | |
| Tokens/Catalan word (avg) | | |
| GPU memory usage | | |
| Model size | | |

### Qualitative Evaluation

Create a test set of prompts and compare responses:

```python
test_prompts = [
    "Responde a un saludo informal en español catalán",
    "Usa expresiones regionales para expresar sorpresa",
    "Despídete de un amigo usando expresiones de Barcelona",
]
```

Rate each response (1-5) on:
1. **Naturalness** - Does it sound like a native speaker?
2. **Regional markers** - Does it use Catalan expressions appropriately?
3. **Grammar** - Is the Spanish grammatically correct?
4. **Appropriateness** - Is it suitable for the scenario?

### A/B Testing with Native Speakers

1. Generate responses from both models for the same prompts
2. Have native speakers rate without knowing which model generated each
3. Calculate preference scores

---

## Hardware Requirements

| Approach | Minimum GPU | Recommended GPU |
|----------|-------------|-----------------|
| Approach 1 (LoRA) | 8GB VRAM | 16GB VRAM |
| Approach 2 (Full) | 16GB VRAM | 24GB+ VRAM |

**For M1/M2/M3 Macs:**
- Use Llama-3.2-1B or 3B models
- Set `--use_4bit` for larger models
- Disable gradient checkpointing (already configured)

---

## Dataset Requirements

### For Fine-tuning (Both Approaches)
- **Format:** JSONL with chat messages
- **Size:** 1,000-10,000 examples recommended
- **Content:** Catalan-accented Spanish conversations
- **Current:** `data/processed/train_catalan_spanish.jsonl`

### For Pre-training (Approach 2 Only)
- **Format:** Plain text files
- **Size:** 10MB-1GB of Catalan/Catalan-Spanish text
- **Sources:**
  - Catalan Wikipedia
  - Catalan news articles
  - Regional Spanish blogs from Catalonia
  - Movie/TV subtitles from Barcelona-set content

---

## Recommended Workflow

1. **Start with Approach 1**
   - Faster to train and evaluate
   - Establish a baseline

2. **Evaluate results with native speakers**
   - Use the audio_recording_prompts.md dialogues
   - Get feedback on regional authenticity

3. **If needed, try Approach 2**
   - Only if Approach 1 shows vocabulary gaps
   - Requires more data and compute

4. **Compare and document results**
   - Fill in the comparison table above
   - Make data-driven decision for production

---

## Files Reference

| File | Purpose |
|------|---------|
| `src/finetune.py` | LoRA fine-tuning script (Approach 1) |
| `src/tokenizer_expansion.py` | Add Catalan tokens (Approach 2, Step 1) |
| `src/pretrain_catalan.py` | Continued pre-training (Approach 2, Step 2) |
| `data/processed/train_catalan_spanish.jsonl` | Training data |
| `data/processed/eval_catalan_spanish.jsonl` | Evaluation data |

---

## References

- [LLaMa2lang - Language Adaptation Pipeline](https://github.com/AI-Commandos/LLaMa2lang)
- [Fine-Tuning Llama 3 with LoRA](https://neptune.ai/blog/fine-tuning-llama-3-with-lora)
- [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory)
- [Official Llama Fine-tuning Guide](https://www.llama.com/docs/how-to-guides/fine-tuning/)
