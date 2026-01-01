# Fluency Evaluation Service

Real-time fluency assessment API for the SpeakEasy language learning app. Evaluates user speech against ground truth movie dialogues and provides comprehensive feedback across 6 metric categories.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Metric Categories](#metric-categories)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Integration Guide](#integration-guide)
- [Testing](#testing)

> **Note:** See [TODO.md](TODO.md) for outstanding tasks including audio file naming fixes and data needed for calibration.

---

## Overview

The Fluency Evaluation Service processes audio recordings of user speech and returns:

- **Composite fluency score** (0-100)
- **CEFR level assessment** (A1-C2)
- **Detailed metrics** across 6 categories
- **Actionable feedback** with practice suggestions

### Key Features

- **Real-time evaluation** (<3 second latency target)
- **OpenAI Whisper** for accurate Spanish speech recognition
- **Word-level timestamps** for precise temporal analysis
- **Catalan expression detection** for regional vocabulary
- **CEFR-aligned scoring** with level-adjusted thresholds

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                          │
│                                                                     │
│  POST /api/v1/fluency/evaluate                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                     Request Handler                            │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                   Audio Processing                             │ │
│  │   M4A → WAV Conversion → Preprocessing → Feature Extraction    │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│              ┌───────────────┼───────────────┐                      │
│              ▼               ▼               ▼                      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐       │
│  │    Whisper      │ │    Feature      │ │   Integration   │       │
│  │  Transcription  │ │   Extractor     │ │    Bridges      │       │
│  │  (word timing)  │ │  (F0, energy)   │ │ (CEFR, Scorer)  │       │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘       │
│              │               │               │                      │
│              └───────────────┼───────────────┘                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                   Fluency Analyzers (Parallel)                 │ │
│  │                                                                │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │ │
│  │  │Pronunciation│  │  Temporal   │  │   Lexical   │            │ │
│  │  │   (0.25)    │  │   (0.20)    │  │   (0.15)    │            │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │ │
│  │  │ Disfluency  │  │  Prosodic   │  │Communicative│            │ │
│  │  │   (0.20)    │  │   (0.10)    │  │   (0.10)    │            │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘            │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    Scoring Engine                              │ │
│  │   Composite Score → Level Thresholds → Feedback Generator      │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    JSON Response                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
src/fluency_service/
├── __init__.py
├── main.py                    # FastAPI entry point
├── config.py                  # Configuration and environment
│
├── api/
│   ├── routes.py              # /evaluate, /health endpoints
│   └── models.py              # Pydantic request/response schemas
│
├── audio/
│   ├── converter.py           # M4A to WAV (FFmpeg)
│   ├── preprocessor.py        # VAD, normalization
│   └── feature_extractor.py   # librosa F0, intensity, formants
│
├── asr/
│   └── whisper_transcriber.py # Whisper with word timestamps
│
├── analyzers/
│   ├── base.py                # BaseAnalyzer interface
│   ├── pronunciation.py       # Phoneme accuracy, Catalan markers
│   ├── temporal.py            # Speaking rate, pauses, latency
│   ├── lexical.py             # WER, expressions, completeness
│   ├── disfluency.py          # Filled pauses, repetitions
│   ├── prosodic.py            # Pitch, rhythm, volume
│   └── communicative.py       # Register, discourse markers
│
├── scoring/
│   ├── composite.py           # Weighted fluency score
│   ├── thresholds.py          # Level-adjusted thresholds
│   └── feedback_generator.py  # Actionable feedback
│
└── integration/
    ├── cefr_bridge.py         # Wraps existing cefr_classifier.py
    ├── response_scorer_bridge.py  # Wraps existing response_scorer.py
    └── ground_truth_loader.py # Loads data/eval/*.json
```

---

## API Reference

### POST `/api/v1/fluency/evaluate`

Evaluate fluency of user audio response.

#### Request

```json
{
  "audio_data": "base64_encoded_audio_or_url",
  "audio_format": "m4a",
  "expected_response": "Hola, nen! Què tal?",
  "scenario": "greetings",
  "user_level": "B2",
  "language": "es-ES",
  "context_before": ["Buenos días"],
  "detailed_feedback": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio_data` | string | Yes | Base64-encoded audio or URL |
| `audio_format` | string | No | Format: m4a, wav, mp3 (default: m4a) |
| `expected_response` | string | No | Ground truth text for comparison |
| `scenario` | string | No | greetings, farewells, family, emotions, plans, requests |
| `user_level` | string | No | CEFR level: A1, A2, B1, B2, C1, C2 (default: B1) |
| `language` | string | No | Language code (default: es-ES) |
| `context_before` | array | No | Previous conversation messages |
| `detailed_feedback` | boolean | No | Include detailed breakdowns (default: true) |

#### Response

```json
{
  "fluency_score": 78.5,
  "level_assessment": "Proficient",
  "cefr_level": "B2",

  "metrics": {
    "pronunciation_accuracy": {
      "score": 82,
      "phoneme_errors": [
        {"word": "perro", "type": "rolled_r", "confidence": 0.65}
      ],
      "catalan_markers": ["nen", "què"],
      "catalan_marker_score": 85,
      "intonation_score": 80,
      "stress_score": 78
    },
    "temporal_metrics": {
      "score": 75,
      "speaking_rate_wpm": 142,
      "target_rate_wpm": 150,
      "pause_analysis": {
        "count": 3,
        "avg_duration_ms": 450,
        "short_pauses": 2,
        "medium_pauses": 1,
        "very_long_pauses": 0
      },
      "response_latency_ms": 650
    },
    "lexical_accuracy": {
      "score": 88,
      "wer": 0.12,
      "catalan_expressions_used": ["nen", "què tal"],
      "catalan_expressions_expected": ["nen", "home"],
      "vocabulary_level": "intermediate"
    },
    "disfluency_detection": {
      "score": 15,
      "filled_pauses": ["um"],
      "filled_pause_count": 1,
      "repetitions": 0,
      "self_corrections": 0,
      "disfluency_rate": 2.1
    },
    "prosodic_quality": {
      "score": 72,
      "pitch_range_hz": [120, 280],
      "pitch_mean_hz": 180,
      "emotional_congruence": 0.78,
      "volume_consistency": 0.85,
      "rhythm_score": 68,
      "pvi": 42
    },
    "communicative_competence": {
      "score": 80,
      "register_match": "informal",
      "register_appropriateness": 0.9,
      "discourse_markers_used": ["bueno", "pues"],
      "turn_taking_score": 75
    }
  },

  "transcript": {
    "text": "Hola, nen! Què tal?",
    "words": [
      {"word": "Hola", "start": 0.0, "end": 0.4, "confidence": 0.98},
      {"word": "nen", "start": 0.5, "end": 0.7, "confidence": 0.95},
      {"word": "Què", "start": 0.8, "end": 1.0, "confidence": 0.92},
      {"word": "tal", "start": 1.0, "end": 1.3, "confidence": 0.97}
    ],
    "language": "es",
    "duration_seconds": 1.5
  },

  "feedback": {
    "summary": "Good conversational fluency with natural Catalan expressions!",
    "strengths": [
      "Natural use of regional vocabulary",
      "Appropriate speaking pace",
      "Clear articulation"
    ],
    "improvements": [
      "Work on rolled 'rr' pronunciation",
      "Reduce filler words"
    ],
    "practice_suggestions": [
      "Practice minimal pairs for sounds you find difficult",
      "Record yourself and compare to native speakers"
    ]
  },

  "processing_time_ms": 1847.3,
  "model_version": "1.0.0"
}
```

### GET `/api/v1/fluency/health`

Health check endpoint.

#### Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "whisper_loaded": true,
  "mfa_available": false,
  "gpu_available": false,
  "uptime_seconds": 3600.5
}
```

### POST `/api/v1/fluency/evaluate/upload`

Alternative endpoint accepting file upload.

```bash
curl -X POST "http://localhost:8001/api/v1/fluency/evaluate/upload" \
     -F "audio_file=@recording.m4a" \
     -F "expected_response=Hola, nen!" \
     -F "scenario=greetings" \
     -F "user_level=B2"
```

---

## Metric Categories

### 1. Pronunciation Accuracy (25% weight)

| Sub-metric | Description | How Measured |
|------------|-------------|--------------|
| Phoneme accuracy | Match to native speaker sounds | ASR confidence scores |
| Catalan marker pronunciation | Correct pronunciation of regional expressions | Binary + quality score |
| Intonation contour | Rising/falling pitch patterns | F0 curve analysis |
| Stress placement | Word stress on correct syllables | Duration variation |

### 2. Temporal Metrics (20% weight)

| Sub-metric | Description | Target |
|------------|-------------|--------|
| Speaking rate | Words per minute | 120-180 WPM for Spanish |
| Pause placement | Natural pauses at phrase boundaries | Match expected patterns |
| Pause duration | Length of pauses | 200-500ms (short), 500-1000ms (medium) |
| Response latency | Time to begin speaking | 200-800ms |

### 3. Lexical Accuracy (15% weight)

| Sub-metric | Description | How Measured |
|------------|-------------|--------------|
| Word accuracy | Correct words spoken | Word Error Rate (WER) |
| Catalan expression usage | Integration of regional markers | Count + appropriateness |
| Phrase completeness | Full dialogue lines delivered | % of expected content |

### 4. Disfluency Detection (20% weight)

| Sub-metric | Description | Target (Advanced) |
|------------|-------------|-------------------|
| Filled pauses | "um", "uh", "eh" frequency | <3 per minute |
| Repetitions | Word/phrase restarts | Minimal |
| Self-corrections | Mid-word/phrase corrections | <2 per minute |
| False starts | Abandoned utterances | <1 per minute |

### 5. Prosodic Quality (10% weight)

| Sub-metric | Description | How Measured |
|------------|-------------|--------------|
| Pitch range | Expressive variation | Standard deviation of F0 |
| Emotional congruence | Tone matches context | Prosody-emotion matching |
| Volume consistency | Stable loudness | dB variance |
| Rhythm naturalness | Syllable timing patterns | PVI (Pairwise Variability Index) |

### 6. Communicative Competence (10% weight)

| Sub-metric | Description | How Measured |
|------------|-------------|--------------|
| Register appropriateness | Formal vs. informal matching | Marker detection |
| Discourse markers | Use of "bueno", "pues", "entonces" | Frequency + placement |
| Turn-taking signals | Natural conversation flow cues | Presence of markers |

### Composite Scoring Formula

```python
FLUENCY_SCORE = (
    0.25 × Pronunciation_Accuracy +
    0.20 × Temporal_Metrics +
    0.15 × Lexical_Accuracy +
    0.20 × (100 - Disfluency_Score) +  # Inverse
    0.10 × Prosodic_Quality +
    0.10 × Communicative_Competence
)
```

### Level-Adjusted Thresholds

| Score Range | B1 Assessment | B2 Assessment |
|-------------|---------------|---------------|
| 90-100 | Native-like | Native-like |
| 75-89 | Proficient | Proficient |
| 60-74 | Developing | Developing |
| <60 | Needs work | Needs work |

---

## Installation

### Prerequisites

- Python 3.9+
- FFmpeg (for audio conversion)
- 4GB+ RAM (for Whisper model)

### Install Dependencies

```bash
# Navigate to dataset-pipeline
cd dataset-pipeline

# Install Python dependencies
pip install -r requirements.txt

# Additional dependencies for fluency service
pip install fastapi uvicorn python-multipart
pip install faster-whisper librosa soundfile praat-parselmouth
pip install webrtcvad jiwer
```

### Install FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows (via chocolatey)
choco install ffmpeg
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | base | Whisper model size: tiny, base, small, medium, large |
| `WHISPER_DEVICE` | cpu | Device: cpu or cuda |
| `API_HOST` | 0.0.0.0 | API host address |
| `API_PORT` | 8001 | API port |

### Configuration File

Edit `config.py` for advanced settings:

```python
@dataclass
class AnalyzerWeights:
    pronunciation: float = 0.25
    temporal: float = 0.20
    lexical: float = 0.15
    disfluency: float = 0.20
    prosodic: float = 0.10
    communicative: float = 0.10
```

---

## Usage Examples

### Start the Server

```bash
# Development mode with auto-reload
uvicorn src.fluency_service.main:app --host 0.0.0.0 --port 8001 --reload

# Production mode
uvicorn src.fluency_service.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### cURL Example

```bash
# Evaluate audio file (base64 encoded)
curl -X POST "http://localhost:8001/api/v1/fluency/evaluate" \
     -H "Content-Type: application/json" \
     -d '{
       "audio_data": "'$(base64 -i recording.m4a)'",
       "audio_format": "m4a",
       "expected_response": "Hola, nen! Què tal?",
       "scenario": "greetings",
       "user_level": "B2"
     }'
```

### Python Client

```python
import requests
import base64

def evaluate_audio(audio_path: str, expected_text: str, level: str = "B1"):
    """Evaluate audio file for fluency."""
    # Read and encode audio
    with open(audio_path, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode("utf-8")

    # Make request
    response = requests.post(
        "http://localhost:8001/api/v1/fluency/evaluate",
        json={
            "audio_data": audio_data,
            "audio_format": "m4a",
            "expected_response": expected_text,
            "user_level": level,
        }
    )

    return response.json()

# Example usage
result = evaluate_audio(
    "recording.m4a",
    "Hola, nen! Què tal?",
    "B2"
)

print(f"Fluency Score: {result['fluency_score']}")
print(f"Assessment: {result['level_assessment']}")
print(f"Feedback: {result['feedback']['summary']}")
```

### JavaScript/TypeScript Client

```typescript
async function evaluateFluency(
  audioBlob: Blob,
  expectedResponse: string,
  userLevel: string = 'B1'
): Promise<FluencyResponse> {
  // Convert blob to base64
  const base64 = await new Promise<string>((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result as string;
      resolve(result.split(',')[1]);
    };
    reader.readAsDataURL(audioBlob);
  });

  const response = await fetch('http://localhost:8001/api/v1/fluency/evaluate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      audio_data: base64,
      audio_format: 'm4a',
      expected_response: expectedResponse,
      user_level: userLevel,
    }),
  });

  return response.json();
}
```

---

## Integration Guide

### Mobile App Integration

1. Record audio in the app (M4A format preferred)
2. Convert to base64 or upload directly
3. Call `/api/v1/fluency/evaluate` endpoint
4. Display results in FeedbackCard component

```typescript
// In Conversation.tsx
const handleSpeechComplete = async (audioBlob: Blob) => {
  const result = await evaluateFluency(audioBlob, expectedResponse, userLevel);

  setFluencyScore(result.fluency_score);
  setFeedback(result.feedback);
  setMetrics(result.metrics);
};
```

### Connecting to Existing Pipeline

The service integrates with existing dataset-pipeline components:

```python
from src.fluency_service.integration.cefr_bridge import get_cefr_bridge
from src.fluency_service.integration.response_scorer_bridge import get_response_scorer

# Use existing CEFR classifier
bridge = get_cefr_bridge()
cefr_result = bridge.classify("Hola, nen!")

# Use existing response scorer
scorer = get_response_scorer()
score_result = scorer.score("Hola, nen!", "Hola, nen! Què tal?", "greetings")
```

---

## Testing

### Run with Example Audio Files

```bash
# Test with files from Example of user response_for eval/
python -c "
from src.fluency_service.audio.converter import convert_to_wav
from src.fluency_service.asr.whisper_transcriber import WhisperTranscriber
from src.fluency_service.audio.feature_extractor import extract_features

# Convert M4A to WAV
convert_to_wav('Example of user response_for eval/beginner_01_greetings.m4a', '/tmp/test.wav')

# Transcribe
transcriber = WhisperTranscriber()
result = transcriber.transcribe('/tmp/test.wav')
print(f'Transcript: {result.text}')

# Extract features
features = extract_features('/tmp/test.wav')
print(f'Duration: {features.duration_seconds}s')
print(f'Pitch mean: {features.pitch_mean}Hz')
"
```

### Health Check

```bash
curl http://localhost:8001/api/v1/fluency/health
```

### Interactive API Docs

Visit `http://localhost:8001/docs` for Swagger UI.

---

## Performance

### Latency Budget

| Component | Target | Typical |
|-----------|--------|---------|
| Audio conversion | <200ms | 100ms |
| Whisper transcription | <1.5s | 800ms |
| Feature extraction | <300ms | 150ms |
| All analyzers | <500ms | 300ms |
| Scoring + feedback | <100ms | 50ms |
| **Total** | **<3s** | **~1.5s** |

### Optimization Tips

1. Use `faster-whisper` instead of `openai-whisper` (4x faster)
2. Use smaller Whisper model (base vs large) for speed
3. Enable GPU if available (`WHISPER_DEVICE=cuda`)
4. Pre-load models at startup (uncomment in `main.py`)

---

## License

Part of the SpeakEasy project. See main repository for license details.
