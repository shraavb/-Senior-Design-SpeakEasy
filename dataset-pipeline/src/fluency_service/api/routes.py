"""
API routes for the Fluency Evaluation Service.
"""

import time
import base64
import tempfile
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from .models import (
    FluencyRequest,
    FluencyResponse,
    HealthResponse,
    ErrorResponse,
    MetricsBreakdown,
    TranscriptResult,
    FeedbackResult,
    WordTimestamp,
    PronunciationMetrics,
    TemporalMetrics,
    LexicalMetrics,
    DisfluencyMetrics,
    ProsodicMetrics,
    CommunicativeMetrics,
)
from ..config import default_config

# Create router
router = APIRouter(prefix="/api/v1/fluency", tags=["fluency"])

# Track service start time
_start_time = time.time()

# Lazy-loaded components (initialized on first request)
_whisper_model = None
_analyzers = None


def get_whisper_model():
    """Lazy-load Whisper model."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from ..asr.whisper_transcriber import WhisperTranscriber
            _whisper_model = WhisperTranscriber(default_config.whisper)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Whisper model not available: {e}")
    return _whisper_model


def get_analyzers():
    """Lazy-load all analyzers."""
    global _analyzers
    if _analyzers is None:
        from ..analyzers import (
            PronunciationAnalyzer,
            TemporalAnalyzer,
            LexicalAnalyzer,
            DisfluencyAnalyzer,
            ProsodicAnalyzer,
            CommunicativeAnalyzer,
        )
        _analyzers = {
            "pronunciation": PronunciationAnalyzer(),
            "temporal": TemporalAnalyzer(),
            "lexical": LexicalAnalyzer(),
            "disfluency": DisfluencyAnalyzer(),
            "prosodic": ProsodicAnalyzer(),
            "communicative": CommunicativeAnalyzer(),
        }
    return _analyzers


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service status and component availability.
    """
    # Check GPU availability
    gpu_available = False
    try:
        import torch
        gpu_available = torch.cuda.is_available()
    except ImportError:
        pass

    # Check if Whisper is loaded
    whisper_loaded = _whisper_model is not None

    # Check MFA availability
    mfa_available = False
    try:
        import subprocess
        result = subprocess.run(["mfa", "version"], capture_output=True)
        mfa_available = result.returncode == 0
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        whisper_loaded=whisper_loaded,
        mfa_available=mfa_available,
        gpu_available=gpu_available,
        uptime_seconds=time.time() - _start_time,
    )


@router.post("/evaluate", response_model=FluencyResponse)
async def evaluate_fluency(request: FluencyRequest) -> FluencyResponse:
    """
    Evaluate fluency of user audio response.

    Analyzes pronunciation, temporal patterns, lexical accuracy,
    disfluencies, prosody, and communicative competence.

    Returns comprehensive metrics and actionable feedback.
    """
    start_time = time.time()

    try:
        # Decode audio data
        audio_path = await _decode_audio(request.audio_data, request.audio_format)

        # Transcribe audio with Whisper
        whisper = get_whisper_model()
        transcript = await asyncio.to_thread(
            whisper.transcribe, str(audio_path)
        )

        # Extract audio features
        from ..audio.feature_extractor import extract_features
        features = await asyncio.to_thread(extract_features, str(audio_path))

        # Run all analyzers in parallel
        analyzers = get_analyzers()
        analysis_tasks = {
            name: asyncio.to_thread(
                analyzer.analyze,
                features,
                transcript,
                request.expected_response,
                request.scenario,
            )
            for name, analyzer in analyzers.items()
        }

        results = {}
        for name, task in analysis_tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                # Return default scores on analyzer failure
                results[name] = {"score": 50.0, "error": str(e)}

        # Build metrics breakdown
        metrics = MetricsBreakdown(
            pronunciation_accuracy=PronunciationMetrics(
                score=results.get("pronunciation", {}).get("score", 50),
                phoneme_errors=results.get("pronunciation", {}).get("phoneme_errors", []),
                catalan_markers=results.get("pronunciation", {}).get("catalan_markers", []),
                catalan_marker_score=results.get("pronunciation", {}).get("catalan_marker_score", 0),
            ),
            temporal_metrics=TemporalMetrics(
                score=results.get("temporal", {}).get("score", 50),
                speaking_rate_wpm=results.get("temporal", {}).get("speaking_rate_wpm", 0),
                pause_analysis=results.get("temporal", {}).get("pause_analysis", {}),
                response_latency_ms=results.get("temporal", {}).get("response_latency_ms"),
            ),
            lexical_accuracy=LexicalMetrics(
                score=results.get("lexical", {}).get("score", 50),
                wer=results.get("lexical", {}).get("wer", 0),
                catalan_expressions_used=results.get("lexical", {}).get("catalan_expressions_used", []),
            ),
            disfluency_detection=DisfluencyMetrics(
                score=results.get("disfluency", {}).get("score", 50),
                filled_pauses=results.get("disfluency", {}).get("filled_pauses", []),
                repetitions=results.get("disfluency", {}).get("repetitions", 0),
            ),
            prosodic_quality=ProsodicMetrics(
                score=results.get("prosodic", {}).get("score", 50),
                pitch_range_hz=results.get("prosodic", {}).get("pitch_range_hz", []),
                rhythm_score=results.get("prosodic", {}).get("rhythm_score", 0),
            ),
            communicative_competence=CommunicativeMetrics(
                score=results.get("communicative", {}).get("score", 50),
                register_match=results.get("communicative", {}).get("register_match", "neutral"),
                discourse_markers_used=results.get("communicative", {}).get("discourse_markers_used", []),
            ),
        )

        # Calculate composite score
        from ..scoring.composite import calculate_composite_score
        fluency_score = calculate_composite_score(metrics, default_config.weights)

        # Get level assessment
        level_assessment = default_config.thresholds.get_assessment(fluency_score)

        # Determine CEFR level
        from ..integration.cefr_bridge import assess_cefr_level
        cefr_level = assess_cefr_level(transcript.text, fluency_score, request.user_level)

        # Generate feedback
        from ..scoring.feedback_generator import generate_feedback
        feedback = generate_feedback(metrics, fluency_score, request.scenario)

        # Build transcript result
        transcript_result = TranscriptResult(
            text=transcript.text,
            words=[
                WordTimestamp(
                    word=w.get("word", ""),
                    start=w.get("start", 0),
                    end=w.get("end", 0),
                    confidence=w.get("confidence", 1.0),
                )
                for w in transcript.words
            ],
            language=transcript.language,
            duration_seconds=transcript.duration,
        )

        # Clean up temp file
        if audio_path.exists():
            audio_path.unlink()

        processing_time = (time.time() - start_time) * 1000

        return FluencyResponse(
            fluency_score=round(fluency_score, 1),
            level_assessment=level_assessment,
            cefr_level=cefr_level,
            metrics=metrics,
            transcript=transcript_result,
            feedback=feedback,
            processing_time_ms=round(processing_time, 1),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate/upload")
async def evaluate_fluency_upload(
    audio_file: UploadFile = File(...),
    expected_response: Optional[str] = Form(None),
    scenario: Optional[str] = Form(None),
    user_level: str = Form("B1"),
) -> FluencyResponse:
    """
    Evaluate fluency from uploaded audio file.

    Alternative endpoint that accepts file upload instead of base64.
    """
    # Read file content
    content = await audio_file.read()
    audio_data = base64.b64encode(content).decode("utf-8")

    # Determine format from filename
    audio_format = "wav"
    if audio_file.filename:
        suffix = Path(audio_file.filename).suffix.lower()
        if suffix in [".m4a", ".mp3", ".wav", ".ogg"]:
            audio_format = suffix[1:]

    # Create request and delegate
    request = FluencyRequest(
        audio_data=audio_data,
        audio_format=audio_format,
        expected_response=expected_response,
        scenario=scenario,
        user_level=user_level,
    )

    return await evaluate_fluency(request)


async def _decode_audio(audio_data: str, audio_format: str) -> Path:
    """
    Decode base64 audio data or download from URL.

    Returns path to temporary audio file.
    """
    temp_dir = default_config.temp_dir

    # Check if it's a URL
    if audio_data.startswith(("http://", "https://")):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_data) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail="Failed to download audio")
                content = await response.read()
    else:
        # Decode base64
        try:
            content = base64.b64decode(audio_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 audio data: {e}")

    # Save to temp file
    temp_path = temp_dir / f"audio_{int(time.time() * 1000)}.{audio_format}"
    temp_path.write_bytes(content)

    # Convert to WAV if needed
    if audio_format != "wav":
        from ..audio.converter import convert_to_wav
        wav_path = temp_dir / f"audio_{int(time.time() * 1000)}.wav"
        await asyncio.to_thread(convert_to_wav, str(temp_path), str(wav_path))
        temp_path.unlink()  # Remove original
        return wav_path

    return temp_path
