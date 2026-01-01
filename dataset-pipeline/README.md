# Catalan-Accented Spanish Dataset Pipeline

A pipeline for building LLM fine-tuning datasets from Spanish movie subtitles, focused on Catalan-accented Spanish for the Personal & Social conversation module.

## Overview

This pipeline:
1. **Downloads** Spanish subtitles from OpenSubtitles API or OPUS corpus
2. **Extracts** clean dialog with timestamps from SRT files
3. **Classifies** dialogs into Personal & Social scenarios (greetings, family, emotions, etc.)
4. **Formats** data into JSONL and CSV for LLM fine-tuning
5. **Generates** evaluation sets for testing

## Quick Start

### 1. Install Dependencies

```bash
cd dataset-pipeline
pip install -r requirements.txt

# For semantic classification (recommended)
pip install sentence-transformers
```

### 2. Set Up API Key (Optional but recommended)

```bash
# Get your API key from https://www.opensubtitles.com/en/consumers
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run the Pipeline

```bash
# Full pipeline (recommended)
python src/main.py all

# Or step by step:
python src/main.py download    # Download subtitles
python src/main.py extract     # Extract dialogs
python src/main.py classify    # Classify scenarios
python src/main.py format      # Create datasets

# Check status
python src/main.py status
```

## Output Files

After running the pipeline, you'll have:

```
data/processed/
├── train_catalan_spanish.jsonl    # Training data for fine-tuning
├── eval_catalan_spanish.jsonl     # Evaluation data
├── catalan_spanish_full.csv       # Full dataset with timestamps
├── eval_prompts.json              # Evaluation prompts
├── eval_greetings.jsonl           # Scenario-specific eval sets
├── eval_family.jsonl
├── eval_emotions.jsonl
└── ...
```

### JSONL Format (for fine-tuning)

```json
{
  "messages": [
    {"role": "system", "content": "You are a native Spanish speaker from Catalonia..."},
    {"role": "user", "content": "Respond to a greeting in Catalan-accented Spanish:"},
    {"role": "assistant", "content": "¡Hola! ¿Qué tal? ¿Cómo va todo?"}
  ],
  "metadata": {
    "scenario": "greetings",
    "confidence": 0.85,
    "source": "Film Title",
    "catalan_markers": ["lexical:apa"]
  }
}
```

### CSV Format (with timestamps)

| id | text | scenario | confidence | source_film | start_timestamp | end_timestamp |
|----|------|----------|------------|-------------|-----------------|---------------|
| film_123 | ¡Hola! ¿Qué tal? | greetings | 0.85 | Film Title | 00:05:23,450 | 00:05:26,120 |

## Personal & Social Scenarios

The classifier identifies these conversation types:

| Scenario | Description | Example Keywords |
|----------|-------------|------------------|
| greetings | Greetings & introductions | hola, buenos días, encantado |
| farewells | Saying goodbye | adiós, hasta luego, cuídate |
| family | Family conversations | mamá, papá, hermano, familia |
| emotions | Expressing feelings | feliz, triste, te quiero |
| opinions | Sharing opinions | creo que, me parece, pienso |
| plans | Making plans | quedamos, vamos a, te apetece |
| requests | Asking for help | puedes, necesito, por favor |
| apologies | Apologies | lo siento, perdona, disculpa |
| small_talk | Casual conversation | qué tiempo, qué tal el trabajo |

## Configuration

Edit `config/settings.yaml` to customize:

- Language filters and Catalan region keywords
- Search parameters (year range, genres)
- Scenario keywords
- Processing thresholds
- Output formats

## Alternative Data Sources

### OPUS Corpus (No API key needed)

```bash
python src/main.py download --method opus
```

This downloads the OpenSubtitles parallel corpus from OPUS, which includes:
- Catalan-Spanish aligned subtitles
- Spanish monolingual subtitle data

### Manual Subtitle Collection

Place `.srt` files directly in `data/raw/` and run:

```bash
python src/main.py extract
python src/main.py classify
python src/main.py format
```

## CEFR Classification & Extended Dialogues

### CEFR Classification

Dialogues are classified according to the Common European Framework of Reference for Languages (CEFR) using a hybrid approach:

1. **Rule-based analysis**: Detects verb tenses, subjunctive mood, sentence complexity
2. **LLM classification**: Uses Claude API for nuanced assessment (when available)

```bash
# Classify dialogues with CEFR levels
python src/cefr_classifier.py
```

| CEFR Level | Simplified | Description |
|------------|------------|-------------|
| A1-A2 | beginner | Present tense, simple sentences |
| B1 | intermediate | Multiple tenses, compound sentences |
| B2 | advanced | Subjunctive, complex clauses |
| C1-C2 | mastery | Literary constructions, sophisticated discourse |

### Extended Multi-Turn Dialogues

Short 1-2 line dialogues were expanded into 10-14 line conversations (5-7 per speaker):

```bash
# Generate extended dialogues
python src/dialogue_expander.py
```

**Training Set** (`data/eval/dialogues_expanded_training.json`):
- LLM-expanded dialogues for model fine-tuning
- 184/204 dialogues expanded successfully
- **20 dialogues used fallback** (original short format) due to API credit exhaustion

**Evaluation Set** (`data/eval/dialogues_merged_eval.json`):
- 4,383 conversation segments merged from 98 movie SRT files
- Authentic movie dialogue for ground truth evaluation
- CEFR-classified using rule-based analysis

### Audio Recording Prompts

Generated prompts for recording gold-standard audio:

| Version | Purpose | Files |
|---------|---------|-------|
| V2 | CEFR-reclassified short dialogues | `audio_recording_prompts_*_v2.md` |
| V3 Training | LLM-expanded multi-turn | `audio_recording_prompts_*_v3_training.md` |
| V3 Eval | Merged movie dialogues | `audio_recording_prompts_*_v3_eval.md` |

### Known Issues

- **API Credit Exhaustion**: 20 training dialogues (indices 185-204) were not LLM-expanded due to Anthropic API credit limits. These use the original short format as fallback. Re-run `dialogue_expander.py` with valid API credits to complete expansion.

## Fine-Tuning with Llama 3

We provide two approaches for fine-tuning Llama models on Catalan-accented Spanish. See the [Fine-Tuning Guide](docs/FINE_TUNING_GUIDE.md) for detailed instructions.

### Approach 1: LoRA Fine-Tuning Only (Recommended to Start)

A simple, fast approach using Low-Rank Adaptation (LoRA) to adapt the model's conversational style.

```bash
python src/finetune.py \
    --model_name meta-llama/Llama-3.2-1B \
    --train_file data/processed/train_catalan_spanish.jsonl \
    --output_dir models/catalan-spanish-lora
```

**Pros:** Fast training (~2-4 hours), works well when tokenizer already handles vocabulary
**Best for:** Quick adaptation, limited compute resources

### Approach 2: Tokenizer Expansion + Pre-training + LoRA

A comprehensive approach for deep dialect specialization:

1. **Expand tokenizer** with Catalan-specific tokens (ostras, nen, apa, etc.)
2. **Continue pre-training** on Catalan text to learn new embeddings
3. **Fine-tune with LoRA** on conversation data

```bash
# Run full pipeline
python src/train_catalan_model.py --approach 2
```

**Pros:** Better handling of regional vocabulary, more authentic dialect representation
**Best for:** Production-grade models, deep dialect specialization

### Comparing Both Approaches

Run both approaches and compare results:

```bash
python src/train_catalan_model.py --compare
```

This generates models from both approaches and saves comparison metrics to `models/comparison_results.json`.

| Approach | Complexity | Training Time | Best For |
|----------|------------|---------------|----------|
| **1: LoRA Only** | Simple | ~2-4 hours | Quick adaptation |
| **2: Full Pipeline** | Advanced | ~8-24 hours | Deep dialect specialization |

## A/B Testing Framework

We provide an A/B testing framework to compare different fine-tuning approaches and measure learning outcomes.

### Available Experiments

| Experiment | Approaches Compared | Purpose |
|------------|---------------------|---------|
| `pilot_v1` | LoRA Only vs Slang-Augmented | Test if slang augmentation improves authenticity |
| `pilot_v2` | Baseline vs LoRA | Test if fine-tuning outperforms prompt engineering |
| `full_comparison` | LoRA vs Tokenizer Expansion | Comprehensive approach comparison |

### Quick Start

```python
from src.ab_testing import ExperimentConfig, assign_user_to_group, MetricsCollector

# Get experiment configuration
config = ExperimentConfig()
experiment = config.get_experiment("pilot_v1")

# Assign user to a group (deterministic)
group = assign_user_to_group("user_123", "pilot_v1")  # Returns "A" or "B"

# Collect metrics
collector = MetricsCollector(experiment_id="pilot_v1")
collector.record_interaction(
    user_id="user_123",
    group=group,
    interaction_type="dialogue_completion",
    metrics={"vocabulary_score": 12, "slang_usage_rate": 0.15}
)
```

See `src/ab_testing/` for full implementation.

## User Evaluation System

We provide a comprehensive evaluation system for measuring user learning outcomes and response quality.

**[Full User Evaluation Documentation](docs/USER_EVALUATION_README.md)**

### Key Features

- **Automatic Response Scoring**: Vocabulary, grammar, slang usage, BLEU score
- **CEFR Level Assessment**: A1-B2 proficiency determination
- **Ground Truth Comparison**: Evaluate against movie dialogue references
- **Good/Bad Response Collection**: For DPO training preparation

### Quick Start

```python
from src.evaluation import ResponseScorer

scorer = ResponseScorer()
result = scorer.score_response(
    user_response="¡Hola, tío! ¿Qué tal todo?",
    scenario="greetings"
)

print(f"Vocabulary Score: {result['vocabulary_score']}")
print(f"Slang Usage: {result['slang_usage_rate']:.1%}")
print(f"CEFR Level: {result['cefr_level']}")
```

### Metrics Tracked

| Metric | Type | Description |
|--------|------|-------------|
| Vocabulary Score | Automatic | Points based on word difficulty (1-4 pts each) |
| Slang Usage Rate | Automatic | Spanish/Catalan slang per total words |
| Regional Authenticity | Human | Catalan markers presence (1-5 scale) |
| Scenario Appropriateness | Human | Response fits context (1-5 scale) |
| BLEU Score | Automatic | Similarity to ground truth responses |

### Loading Data

```python
from datasets import load_dataset

dataset = load_dataset('json', data_files={
    'train': 'data/processed/train_catalan_spanish.jsonl',
    'eval': 'data/processed/eval_catalan_spanish.jsonl'
})
```

## Fluency Evaluation Service

Real-time fluency assessment API for evaluating user speech against ground truth movie dialogues.

**[Full Fluency Service Documentation](src/fluency_service/README.md)**

### Key Features

- **6 Metric Categories**: Pronunciation, Temporal, Lexical, Disfluency, Prosodic, Communicative
- **Whisper ASR**: Word-level timestamps for precise analysis
- **CEFR-Aligned**: Level-adjusted scoring thresholds (A1-C2)
- **Catalan Detection**: Regional expression scoring

### Quick Start

```bash
# Start the service
uvicorn src.fluency_service.main:app --host 0.0.0.0 --port 8001

# Evaluate audio
curl -X POST "http://localhost:8001/api/v1/fluency/evaluate" \
     -H "Content-Type: application/json" \
     -d '{"audio_data": "<base64>", "expected_response": "Hola, nen!"}'
```

### Composite Scoring Formula

```
FLUENCY_SCORE = (
    0.25 × Pronunciation +
    0.20 × Temporal +
    0.15 × Lexical +
    0.20 × (100 - Disfluency) +
    0.10 × Prosodic +
    0.10 × Communicative
)
```

## Cloud GPU Deployment

For training on cloud A100 GPUs, see the [RunPod Deployment Guide](deploy/README.md).

Quick start:
```bash
# Upload to RunPod
runpodctl send deploy/runpod_upload.zip

# On RunPod terminal
bash setup_and_train.sh
python runpod_train.py --quick  # 1 epoch, ~30 min
```

## High-Performance Inference

For production inference, we support:

- **vLLM**: High-throughput inference with PagedAttention (`src/inference_vllm.py`)
- **SGLang**: Structured generation with RadixAttention (`src/inference_sglang.py`)
- **Modal**: Serverless GPU deployment (`deploy/modal_deploy.py`)

```bash
# vLLM server
python src/inference_vllm.py serve --port 8000

# SGLang batch inference
python src/inference_sglang.py batch --input prompts.json
```

## Catalan Markers Detection

The pipeline identifies Catalan influence in Spanish through:

- **Lexical borrowings**: nen/nena, home, ostras, apa
- **Syntactic patterns**: "hacer broma" instead of "gastar broma"
- **Regional expressions**: Common Catalan-influenced phrases

These markers are included in the metadata for filtering and analysis.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  OpenSubtitles  │────▶│  SRT Parser      │────▶│  Scenario       │
│  Downloader     │     │  & Extractor     │     │  Classifier     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Eval Set       │◀────│  Dataset         │◀────│  JSONL/CSV      │
│  Generator      │     │  Formatter       │     │  Output         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## License

MIT License - See LICENSE file
