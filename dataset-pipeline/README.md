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

### Loading Data

```python
from datasets import load_dataset

dataset = load_dataset('json', data_files={
    'train': 'data/processed/train_catalan_spanish.jsonl',
    'eval': 'data/processed/eval_catalan_spanish.jsonl'
})
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
