# Fluency Service - Outstanding Tasks

## 1. Audio File Naming Mismatch (NEEDS FIXING)

### Problem
The audio files in `Example of user response_for eval/` use **sequential numbering**:
```
beginner_01_greetings.m4a
beginner_02_greetings.m4a
beginner_03_greetings.m4a  ← 3 greetings files
beginner_04_farewells.m4a  ← only 1 farewell file
...
```

But the prompt files use **per-category numbering**:
```
Greetings 01, Greetings 02  (2 dialogues)
Farewells 01, Farewells 02  (2 dialogues)
...
```

### Current Audio Files
```
BEGINNER (12 files):
├── beginner_01_greetings.m4a  → Greetings 01?
├── beginner_02_greetings.m4a  → Greetings 02?
├── beginner_03_greetings.m4a  → ??? (only 2 greetings in prompt)
├── beginner_04_farewells.m4a  → Farewells 01?
├── beginner_05_family.m4a     → Family 01?
├── beginner_06_family.m4a     → Family 02?
├── beginner_07_emotions.m4a   → Emotions 01?
├── beginner_08_emotions.m4a   → Emotions 02?
├── beginner_09_plans.m4a      → Plans 01?
├── beginner_10_plans.m4a      → Plans 02?
├── beginner_11_requests.m4a   → Requests 01?
└── beginner_12_requests.m4a   → Requests 02?

INTERMEDIATE (12 files):
├── intermediate_01_greetings.m4a
├── intermediate_02_greetings.m4a
├── intermediate_03_farewells.m4a
├── intermediate_04_farewells.m4a
├── intermediate_05_family.m4a
├── intermediate_06_family.m4a
├── intermediate_07_emotions.m4a
├── intermediate_08_emotions.m4a
├── intermediate_09_plans.m4a
├── intermediate_10_plans.m4a
├── intermediate_11_requests.m4a
└── intermediate_12_requests.m4a

ADVANCED (11 files - missing one):
├── advanced_01_greetings.m4a
├── advanced_02_greetings.m4a
├── advanced_03_farewells.m4a  ← only 1 farewell (prompt has 2)
├── advanced_04_family.m4a
├── advanced_05_family.m4a
├── advanced_06_emotions.m4a
├── advanced_07_emotions.m4a
├── advanced_08_plans.m4a
├── advanced_09_plans.m4a
├── advanced_10_requests.m4a
└── advanced_11_requests.m4a
```

### Action Required
**Option A: Fix file names** to match prompt format:
```
beginner_greetings_01.m4a  (matches "Greetings 01")
beginner_greetings_02.m4a  (matches "Greetings 02")
beginner_farewells_01.m4a  (matches "Farewells 01")
...
```

**Option B: Create explicit mapping file** linking each audio to its prompt dialogue.

---

## 2. Data Needed for Calibration

### High Priority
- [ ] **Human fluency ratings** (0-100) for each of the 35 audio files
- [ ] **Verify audio-to-prompt mapping** - which audio file corresponds to which dialogue

### Medium Priority
- [ ] **Bad/poor quality examples** - recordings with:
  - Excessive disfluencies (many "um", "uh")
  - Pronunciation errors (wrong rolled "rr", "j" sounds)
  - Wrong register (too formal/informal for context)
  - Very slow speech with long pauses

### Nice to Have
- [ ] **Native speaker reference recordings** for each prompt (gold standard)
- [ ] **Recordings at different CEFR levels** (A1, A2, B1, B2, C1) for threshold calibration

---

## 3. Ground Truth Mapping Template

Create a file `ground_truth_mapping.json` with this structure:

```json
{
  "beginner_01_greetings.m4a": {
    "prompt_file": "audio_recording_prompts_beginner.md",
    "dialogue_id": "Greetings 01",
    "source": "To Barcelona with Love (01:00:58,363)",
    "transcript": "A: Nico. B: Esto parece increíble. A: Anna. Hola. B: Pensé que estabas en el hotel escribiendo. A: Yo también.",
    "human_rating": null,
    "notes": ""
  }
}
```

---

## 4. Service Dependencies to Install

Before running the service:

```bash
pip install fastapi uvicorn python-multipart
pip install faster-whisper  # or openai-whisper
pip install librosa soundfile praat-parselmouth
pip install webrtcvad jiwer

# System dependency
brew install ffmpeg  # macOS
# apt install ffmpeg  # Ubuntu
```

---

## 5. Quick Test

Once dependencies are installed:

```bash
cd dataset-pipeline
uvicorn src.fluency_service.main:app --port 8001

# Visit http://localhost:8001/docs for API docs
# Health check: http://localhost:8001/api/v1/fluency/health
```

---

## Contact / Questions

If you have questions about the fluency service implementation, check:
- `src/fluency_service/README.md` - Full documentation
- `src/fluency_service/config.py` - Weights and thresholds configuration
