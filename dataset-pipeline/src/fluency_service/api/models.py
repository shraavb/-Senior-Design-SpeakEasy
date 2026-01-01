"""
Pydantic models for the Fluency Evaluation API.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ============== Request Models ==============

class FluencyRequest(BaseModel):
    """Request model for fluency evaluation."""
    audio_data: str = Field(
        ...,
        description="Base64-encoded audio data or URL to audio file"
    )
    audio_format: str = Field(
        default="m4a",
        description="Audio format: m4a, wav, mp3"
    )
    expected_response: Optional[str] = Field(
        default=None,
        description="Ground truth text for comparison"
    )
    scenario: Optional[str] = Field(
        default=None,
        description="Conversation scenario: greetings, farewells, family, emotions, plans, requests"
    )
    user_level: str = Field(
        default="B1",
        description="User's CEFR level: A1, A2, B1, B2, C1, C2"
    )
    language: str = Field(
        default="es-ES",
        description="Language code"
    )
    context_before: Optional[List[str]] = Field(
        default=None,
        description="Previous conversation messages for context"
    )
    detailed_feedback: bool = Field(
        default=True,
        description="Whether to include detailed metric breakdowns"
    )


# ============== Response Models ==============

class WordTimestamp(BaseModel):
    """Word with timing information."""
    word: str
    start: float
    end: float
    confidence: float = 1.0


class TranscriptResult(BaseModel):
    """Transcription result with word-level timestamps."""
    text: str
    words: List[WordTimestamp]
    language: str = "es"
    duration_seconds: float = 0.0


class PronunciationMetrics(BaseModel):
    """Pronunciation accuracy metrics."""
    score: float = Field(..., ge=0, le=100)
    phoneme_errors: List[Dict[str, str]] = Field(default_factory=list)
    catalan_markers: List[str] = Field(default_factory=list)
    catalan_marker_score: float = Field(default=0, ge=0, le=100)
    intonation_score: float = Field(default=0, ge=0, le=100)
    stress_score: float = Field(default=0, ge=0, le=100)


class TemporalMetrics(BaseModel):
    """Temporal/timing metrics."""
    score: float = Field(..., ge=0, le=100)
    speaking_rate_wpm: float = Field(default=0, ge=0)
    target_rate_wpm: float = Field(default=150)
    pause_analysis: Dict[str, Any] = Field(default_factory=dict)
    response_latency_ms: Optional[float] = None
    total_speech_duration_ms: float = 0
    total_pause_duration_ms: float = 0


class LexicalMetrics(BaseModel):
    """Lexical accuracy metrics."""
    score: float = Field(..., ge=0, le=100)
    wer: float = Field(default=0, ge=0, le=1, description="Word Error Rate")
    catalan_expressions_used: List[str] = Field(default_factory=list)
    catalan_expressions_expected: List[str] = Field(default_factory=list)
    expected_phrases_hit: int = 0
    expected_phrases_total: int = 0
    vocabulary_level: str = "intermediate"


class DisfluencyMetrics(BaseModel):
    """Disfluency detection metrics."""
    score: float = Field(..., ge=0, le=100, description="Lower is better (fewer disfluencies)")
    filled_pauses: List[str] = Field(default_factory=list)
    filled_pause_count: int = 0
    repetitions: int = 0
    self_corrections: int = 0
    false_starts: int = 0
    disfluency_rate: float = Field(default=0, description="Disfluencies per minute")


class ProsodicMetrics(BaseModel):
    """Prosodic quality metrics."""
    score: float = Field(..., ge=0, le=100)
    pitch_range_hz: List[float] = Field(default_factory=list)
    pitch_mean_hz: float = 0
    pitch_std_hz: float = 0
    emotional_congruence: float = Field(default=0, ge=0, le=1)
    volume_consistency: float = Field(default=0, ge=0, le=1)
    rhythm_score: float = Field(default=0, ge=0, le=100)
    pvi: float = Field(default=0, description="Pairwise Variability Index")


class CommunicativeMetrics(BaseModel):
    """Communicative competence metrics."""
    score: float = Field(..., ge=0, le=100)
    register_match: str = Field(default="neutral")
    register_appropriateness: float = Field(default=0, ge=0, le=1)
    discourse_markers_used: List[str] = Field(default_factory=list)
    discourse_markers_expected: List[str] = Field(default_factory=list)
    turn_taking_score: float = Field(default=0, ge=0, le=100)


class MetricsBreakdown(BaseModel):
    """Complete breakdown of all fluency metrics."""
    pronunciation_accuracy: PronunciationMetrics
    temporal_metrics: TemporalMetrics
    lexical_accuracy: LexicalMetrics
    disfluency_detection: DisfluencyMetrics
    prosodic_quality: ProsodicMetrics
    communicative_competence: CommunicativeMetrics


class FeedbackResult(BaseModel):
    """Human-readable feedback for the user."""
    summary: str
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    practice_suggestions: List[str] = Field(default_factory=list)


class FluencyResponse(BaseModel):
    """Complete response from fluency evaluation."""
    fluency_score: float = Field(..., ge=0, le=100)
    level_assessment: str = Field(..., description="Native-like, Proficient, Developing, Needs work")
    cefr_level: str = Field(..., description="Assessed CEFR level: A1-C2")

    metrics: MetricsBreakdown
    transcript: TranscriptResult
    feedback: FeedbackResult

    processing_time_ms: float = 0
    model_version: str = "1.0.0"


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    whisper_loaded: bool = False
    mfa_available: bool = False
    gpu_available: bool = False
    uptime_seconds: float = 0


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    status_code: int = 500
