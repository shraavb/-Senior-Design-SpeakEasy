# User Response Evaluation System

This document describes how user responses are evaluated against ground truth dialogues in the SpeakEasy Catalan-Spanish language learning platform.

## Table of Contents

1. [Overview](#overview)
2. [Evaluation Metrics](#evaluation-metrics)
3. [Ground Truth Data](#ground-truth-data)
4. [Scoring System](#scoring-system)
5. [Good vs Bad Response Examples](#good-vs-bad-response-examples)
6. [A/B Testing Framework](#ab-testing-framework)
7. [API Reference](#api-reference)
8. [Collection Guidelines](#collection-guidelines)

---

## Overview

The evaluation system measures user language learning progress by comparing their responses against authentic movie/TV dialogue (ground truth). This enables:

- **Automatic scoring** of vocabulary, grammar, and slang usage
- **CEFR level assessment** (A1 → B2)
- **Regional authenticity** measurement for Catalan-accented Spanish
- **A/B testing** of different fine-tuning approaches

### Evaluation Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  User Response  │────▶│  Preprocessing   │────▶│  Feature        │
│                 │     │  (tokenize,      │     │  Extraction     │
└─────────────────┘     │  normalize)      │     └────────┬────────┘
                        └──────────────────┘              │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Final Score    │◀────│  Comparison      │◀────│  Ground Truth   │
│  + Feedback     │     │  Engine          │     │  Database       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## Evaluation Metrics

### 1. Automatic Metrics

#### Vocabulary Score (0-15 points)

Points awarded based on word difficulty level:

| Level | Points | Example Words |
|-------|--------|---------------|
| Beginner | 1 | hola, adiós, mamá, papá |
| Intermediate | 2 | quedamos, encantado, preocupado |
| Advanced | 3 | parientes, suegros, aliviado |
| Regional/Slang | 4 | nen, nena, hostia, mola, flipar |

**Formula:**
```
vocabulary_score = (beginner_count × 1) + (intermediate_count × 2) +
                   (advanced_count × 3) + (regional_count × 4)
```

#### Slang Usage Rate

Measures authentic colloquial language usage:

```python
spanish_slang_rate = spanish_slang_words / total_words
catalan_slang_rate = catalan_slang_words / total_words
combined_slang_rate = (spanish_slang + catalan_slang) / total_words
```

**Spanish Slang Terms Tracked:**
- Common: vale, guay, mola, genial, flipar, curro, pasta, quedamos
- Reactions: hostia, joder, qué pasada, alucinar
- Social: tío/tía, chaval, colega, botellón, marcha

**Catalan Slang Terms Tracked:**
- Address: nen, nena, nano, home
- Reactions: hòstia, collons, quina passada, flipar, de debò
- Social: quedem, sortir de festa, fer el vermut, calés

#### Response Similarity

**BLEU Score** (0-1):
```python
from nltk.translate.bleu_score import sentence_bleu
bleu = sentence_bleu([ground_truth_tokens], user_tokens)
```

**Semantic Similarity** (0-1):
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
similarity = cosine_similarity(
    model.encode(user_response),
    model.encode(ground_truth)
)
```

#### Grammar Score (0-100)

Automated grammar checking using SpaCy:

| Check | Weight | Description |
|-------|--------|-------------|
| Subject-verb agreement | 25% | "Yo soy" vs "Yo es" |
| Verb tense consistency | 25% | Mixing past/present inappropriately |
| Gender/number agreement | 25% | "La problema" vs "El problema" |
| Formality consistency | 25% | Mixing tú/usted inappropriately |

### 2. Human/Crowdsourced Metrics

Collected via Prolific/MTurk using `data/eval/crowdsourcing_task.csv`:

| Metric | Scale | Description |
|--------|-------|-------------|
| Naturalness | 1-5 | Does it sound like a native speaker? |
| Regional Authenticity | 1-5 | Does it reflect Catalan-accented Spanish? |
| Scenario Appropriateness | 1-5 | Does the response fit the conversation context? |
| Grammar Quality | 1-5 | Is the grammar correct? |

### 3. Engagement Metrics

Tracked by the web platform:

| Metric | Description | Target |
|--------|-------------|--------|
| Time per dialogue | Seconds spent on each response | 30-120s |
| Completion rate | % of dialogues completed | >80% |
| Return visits | Sessions per user per week | 3+ |
| Self-reported confidence | Pre/post survey (1-10) | +2 improvement |

---

## Ground Truth Data

### Source
Ground truth responses are extracted from authentic movie/TV subtitles:

- **Films**: Vicky Cristina Barcelona, Spanish Affair, Barcelona Summer Night, Merlí
- **Total dialogues**: 2,041 evaluation examples
- **Scenarios**: 9 categories (greetings, farewells, family, emotions, opinions, plans, requests, apologies, small_talk)

### Data Location

| File | Description | Format |
|------|-------------|--------|
| `data/eval/model_eval_ground_truth.json` | Ground truth with context | JSON |
| `data/processed/eval_*.jsonl` | Scenario-specific eval sets | JSONL |
| `data/eval/scenario_vocabulary.json` | Expected vocabulary per scenario | JSON |

### Ground Truth Structure

```json
{
  "id": "Film_Title_2008_123",
  "scenario": "greetings",
  "prompt": "Respond to a greeting in Catalan-accented Spanish:\nContext: Meeting a friend on the street",
  "ground_truth": "¡Hola! ¿Qué tal, nen? ¿Cómo va todo?",
  "context_before": ["¿Eres Vicky?", "Sí, Vicky."],
  "context_after": ["Bien, muy bien.", "Me alegro de verte."],
  "source_film": "Vicky Cristina Barcelona",
  "expected_vocabulary": {
    "beginner": ["hola", "bien"],
    "intermediate": ["qué tal", "cómo va"],
    "advanced": [],
    "catalan_regional": ["nen"]
  }
}
```

---

## Scoring System

### CEFR Level Mapping

| Level | Vocabulary Score | Grammar Score | Description |
|-------|-----------------|---------------|-------------|
| A1 (Basic) | 1-3 | 40-60 | Basic phrases, simple vocabulary |
| A2 (Elementary) | 3-6 | 60-70 | Everyday expressions, simple sentences |
| B1 (Intermediate) | 6-10 | 70-85 | Clear standard speech, familiar topics |
| B2 (Upper-Int) | 10-15 | 85-100 | Complex text, spontaneous interaction |

### Composite Score Calculation

```python
def calculate_composite_score(metrics):
    weights = {
        'vocabulary_score': 0.25,
        'slang_rate': 0.15,
        'bleu_score': 0.15,
        'semantic_similarity': 0.15,
        'grammar_score': 0.20,
        'human_naturalness': 0.10
    }

    composite = sum(
        metrics[key] * weight
        for key, weight in weights.items()
    )
    return composite
```

---

## Good vs Bad Response Examples

### Collection Purpose
Good/bad response pairs enable:
1. **User feedback**: Show learners what to aim for
2. **DPO training**: Direct Preference Optimization for model improvement
3. **Rubric calibration**: Align automatic scores with human judgment

### Example Structure

**Location**: `data/eval/good_responses.json` and `data/eval/bad_responses.json`

```json
{
  "scenario": "greetings",
  "prompt": "Say hello to a friend you haven't seen in a while",
  "context": "Casual street encounter in Barcelona",
  "good_response": {
    "text": "¡Ei, nen! Què tal? Fa temps que no et veig! Com va tot?",
    "why_good": [
      "Uses Catalan greeting 'Ei'",
      "Regional address 'nen'",
      "Natural follow-up questions",
      "Appropriate informality"
    ],
    "vocabulary_level": "advanced",
    "slang_used": ["nen", "què tal"]
  },
  "bad_response": {
    "text": "Hola. ¿Cómo está usted?",
    "why_bad": [
      "Too formal (usted) for friends",
      "No regional markers",
      "Lacks warmth/enthusiasm",
      "Generic, not Catalan-influenced"
    ],
    "issues": ["formality_mismatch", "no_regional_markers"]
  }
}
```

### Collection Guidelines

When collecting good/bad examples:

**Good Responses Should:**
- Use appropriate slang for the scenario
- Match the formality level (tú for friends, usted for formal)
- Include Catalan regional markers naturally
- Sound like a native Barcelona speaker
- Be contextually appropriate

**Bad Responses May Have:**
- Wrong formality level
- Missing regional authenticity
- Grammar errors
- Inappropriate vocabulary
- Off-topic or awkward phrasing

---

## A/B Testing Framework

### Current Experiments

| Experiment | Approach A | Approach B | Hypothesis |
|------------|------------|------------|------------|
| Pilot v1 | A1: LoRA Only | A3: Slang-Augmented LoRA | Slang augmentation improves authenticity |

### Approaches Being Tested

| ID | Approach | Description | Training Data |
|----|----------|-------------|---------------|
| A1 | LoRA Only | Direct fine-tuning | 11,524 dialogues |
| A2 | Tokenizer Expansion | Deep specialization | 11,524 + Catalan corpus |
| A3 | Slang-Augmented | LoRA + synthetic slang | 11,594 dialogues (11,524 + 70 synthetic) |
| A4 | Baseline | No fine-tuning | None (prompt engineering) |

### User Assignment

```python
import hashlib

def assign_user_to_group(user_id, experiment_id):
    """Deterministic assignment based on user ID"""
    hash_input = f"{user_id}:{experiment_id}"
    hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
    return "A" if hash_value % 2 == 0 else "B"
```

### Metrics Tracked Per Group

| Metric Category | Specific Metrics |
|-----------------|------------------|
| Learning Outcomes | Vocabulary score improvement, CEFR level progression |
| Authenticity | Slang usage rate, regional marker frequency |
| Engagement | Time spent, completion rate, return visits |
| Satisfaction | Self-reported confidence, NPS score |

### Statistical Analysis

For pilot (5-10 users per group):
- Use non-parametric tests (Mann-Whitney U)
- Calculate effect sizes (Cohen's d)
- Report confidence intervals
- Acknowledge limited statistical power

---

## API Reference

### Response Scoring API

```python
from src.evaluation.response_scorer import ResponseScorer

scorer = ResponseScorer()

# Score a single response
result = scorer.score(
    user_response="¡Hola, nen! ¿Qué tal?",
    ground_truth="¡Hola! ¿Qué tal, nen? ¿Cómo va todo?",
    scenario="greetings"
)

# Result structure
{
    "vocabulary_score": 8,
    "vocabulary_breakdown": {
        "beginner": ["hola"],
        "intermediate": ["qué tal"],
        "regional": ["nen"]
    },
    "slang_rate": {
        "spanish": 0.0,
        "catalan": 0.25,
        "combined": 0.25
    },
    "bleu_score": 0.72,
    "semantic_similarity": 0.89,
    "grammar_score": 95,
    "cefr_level": "B1",
    "composite_score": 0.78,
    "feedback": [
        "Good use of Catalan address term 'nen'",
        "Consider adding follow-up questions for more natural flow"
    ]
}
```

### Batch Evaluation

```python
from src.evaluation.metrics import evaluate_batch

results = evaluate_batch(
    responses_file="user_responses.jsonl",
    ground_truth_file="data/eval/model_eval_ground_truth.json"
)

# Export for analysis
results.to_csv("evaluation_results.csv")
```

---

## Collection Guidelines

### For Crowdsourced Evaluation

1. **Platform**: Prolific (recommended) or MTurk
2. **Task file**: `data/eval/crowdsourcing_task.csv`
3. **Time per task**: ~2-3 minutes
4. **Payment**: $0.50-1.00 per task

### Evaluator Instructions

> You will see a conversation context and two responses. Rate each response on:
> 1. **Naturalness** (1-5): Does it sound like a native speaker?
> 2. **Regional Authenticity** (1-5): Does it sound like someone from Barcelona/Catalonia?
> 3. **Scenario Appropriateness** (1-5): Does the response fit the conversation?
> 4. **Grammar** (1-5): Is the grammar correct?

### Quality Control

- Include 10% attention check questions
- Require Spanish language proficiency (B2+)
- Prefer evaluators from Spain/Catalonia
- Cross-validate with multiple evaluators (3+ per response)

---

## File Reference

| File | Purpose |
|------|---------|
| `src/evaluation/response_scorer.py` | Main scoring implementation |
| `src/evaluation/metrics.py` | Metric definitions and calculations |
| `data/eval/good_responses.json` | Curated good response examples |
| `data/eval/bad_responses.json` | Curated bad response examples |
| `data/eval/scenario_vocabulary.json` | Expected vocabulary per scenario |
| `data/eval/user_assessment_rubrics.json` | Detailed scoring rubrics |
| `data/eval/cefr_rubrics.json` | CEFR level definitions |
| `data/eval/crowdsourcing_task.csv` | Template for human evaluation |
| `src/ab_testing/experiment_config.py` | A/B test configuration |

---

## Related Documentation

- [Fine-Tuning Guide](FINE_TUNING_GUIDE.md) - Training approaches
- [Main README](../README.md) - Pipeline overview
- [Catalan Subtitle Sources](../data/catalan_subtitle_sources.md) - Data expansion
