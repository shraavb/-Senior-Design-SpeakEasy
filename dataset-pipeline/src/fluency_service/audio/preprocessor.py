"""
Audio preprocessing utilities.

Handles normalization, Voice Activity Detection (VAD), and silence trimming.
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    logger.warning("webrtcvad not available - VAD features disabled")

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    logger.warning("soundfile not available")


@dataclass
class VoiceSegment:
    """A segment of detected voice activity."""
    start_ms: float
    end_ms: float
    duration_ms: float

    @property
    def start_seconds(self) -> float:
        return self.start_ms / 1000.0

    @property
    def end_seconds(self) -> float:
        return self.end_ms / 1000.0


def load_audio(audio_path: str, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    """
    Load audio file and resample if needed.

    Args:
        audio_path: Path to audio file
        target_sr: Target sample rate

    Returns:
        Tuple of (audio_data, sample_rate)
    """
    if not SOUNDFILE_AVAILABLE:
        raise ImportError("soundfile is required for audio loading")

    audio, sr = sf.read(audio_path)

    # Convert stereo to mono
    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)

    # Resample if needed
    if sr != target_sr:
        try:
            import librosa
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
        except ImportError:
            logger.warning(f"librosa not available, using original sample rate {sr}")

    return audio.astype(np.float32), sr


def normalize_audio(audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
    """
    Normalize audio to target dB level.

    Args:
        audio: Audio data as numpy array
        target_db: Target dB level (default: -20 dB)

    Returns:
        Normalized audio data
    """
    # Calculate current RMS
    rms = np.sqrt(np.mean(audio ** 2))

    if rms < 1e-10:
        return audio  # Silent audio, don't normalize

    # Calculate current dB
    current_db = 20 * np.log10(rms)

    # Calculate gain
    gain_db = target_db - current_db
    gain = 10 ** (gain_db / 20)

    # Apply gain
    normalized = audio * gain

    # Prevent clipping
    max_val = np.max(np.abs(normalized))
    if max_val > 1.0:
        normalized = normalized / max_val

    return normalized


def detect_voice_activity(
    audio: np.ndarray,
    sample_rate: int = 16000,
    aggressiveness: int = 2,
    frame_duration_ms: int = 30,
) -> List[VoiceSegment]:
    """
    Detect voice activity segments using WebRTC VAD.

    Args:
        audio: Audio data as numpy array (float32, normalized to [-1, 1])
        sample_rate: Sample rate (must be 8000, 16000, 32000, or 48000)
        aggressiveness: VAD aggressiveness (0-3, higher = more aggressive)
        frame_duration_ms: Frame duration (10, 20, or 30 ms)

    Returns:
        List of VoiceSegment objects
    """
    if not VAD_AVAILABLE:
        logger.warning("VAD not available, returning full audio as voice")
        duration_ms = len(audio) / sample_rate * 1000
        return [VoiceSegment(0, duration_ms, duration_ms)]

    # Validate sample rate
    if sample_rate not in [8000, 16000, 32000, 48000]:
        logger.warning(f"Invalid sample rate {sample_rate} for VAD, skipping")
        duration_ms = len(audio) / sample_rate * 1000
        return [VoiceSegment(0, duration_ms, duration_ms)]

    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)

    # Create VAD
    vad = webrtcvad.Vad(aggressiveness)

    # Calculate frame size
    frame_size = int(sample_rate * frame_duration_ms / 1000)

    # Process frames
    voice_frames = []
    for i in range(0, len(audio_int16) - frame_size, frame_size):
        frame = audio_int16[i:i + frame_size]
        is_speech = vad.is_speech(frame.tobytes(), sample_rate)
        voice_frames.append((i, is_speech))

    # Merge consecutive voice frames into segments
    segments = []
    in_voice = False
    segment_start = 0

    for frame_idx, is_speech in voice_frames:
        frame_ms = frame_idx / sample_rate * 1000

        if is_speech and not in_voice:
            # Start of voice segment
            segment_start = frame_ms
            in_voice = True
        elif not is_speech and in_voice:
            # End of voice segment
            segment_end = frame_ms
            duration = segment_end - segment_start
            if duration > 50:  # Minimum 50ms segment
                segments.append(VoiceSegment(segment_start, segment_end, duration))
            in_voice = False

    # Handle case where audio ends during voice
    if in_voice:
        segment_end = len(audio) / sample_rate * 1000
        duration = segment_end - segment_start
        if duration > 50:
            segments.append(VoiceSegment(segment_start, segment_end, duration))

    return segments


def trim_silence(
    audio: np.ndarray,
    sample_rate: int = 16000,
    threshold_db: float = -40.0,
    min_silence_ms: int = 100,
) -> Tuple[np.ndarray, float, float]:
    """
    Trim leading and trailing silence from audio.

    Args:
        audio: Audio data as numpy array
        sample_rate: Sample rate
        threshold_db: Silence threshold in dB
        min_silence_ms: Minimum silence duration to consider

    Returns:
        Tuple of (trimmed_audio, start_trim_ms, end_trim_ms)
    """
    # Convert threshold to amplitude
    threshold = 10 ** (threshold_db / 20)

    # Calculate frame size
    frame_size = int(sample_rate * min_silence_ms / 1000)

    # Find start (first frame above threshold)
    start_sample = 0
    for i in range(0, len(audio) - frame_size, frame_size):
        frame_rms = np.sqrt(np.mean(audio[i:i + frame_size] ** 2))
        if frame_rms > threshold:
            start_sample = max(0, i - frame_size)  # Keep a bit of lead-in
            break

    # Find end (last frame above threshold)
    end_sample = len(audio)
    for i in range(len(audio) - frame_size, frame_size, -frame_size):
        frame_rms = np.sqrt(np.mean(audio[i:i + frame_size] ** 2))
        if frame_rms > threshold:
            end_sample = min(len(audio), i + 2 * frame_size)  # Keep a bit of trail
            break

    # Trim
    trimmed = audio[start_sample:end_sample]
    start_trim_ms = start_sample / sample_rate * 1000
    end_trim_ms = (len(audio) - end_sample) / sample_rate * 1000

    return trimmed, start_trim_ms, end_trim_ms


def preprocess_audio(
    audio_path: str,
    normalize: bool = True,
    trim: bool = True,
    target_sr: int = 16000,
) -> Tuple[np.ndarray, int, dict]:
    """
    Full preprocessing pipeline for audio.

    Args:
        audio_path: Path to audio file
        normalize: Whether to normalize volume
        trim: Whether to trim silence
        target_sr: Target sample rate

    Returns:
        Tuple of (processed_audio, sample_rate, metadata)
    """
    # Load audio
    audio, sr = load_audio(audio_path, target_sr)

    metadata = {
        "original_duration_ms": len(audio) / sr * 1000,
        "sample_rate": sr,
    }

    # Trim silence
    if trim:
        audio, start_trim, end_trim = trim_silence(audio, sr)
        metadata["start_trim_ms"] = start_trim
        metadata["end_trim_ms"] = end_trim

    # Normalize
    if normalize:
        audio = normalize_audio(audio)
        metadata["normalized"] = True

    # Detect voice activity
    voice_segments = detect_voice_activity(audio, sr)
    metadata["voice_segments"] = len(voice_segments)
    metadata["total_voice_ms"] = sum(s.duration_ms for s in voice_segments)

    metadata["processed_duration_ms"] = len(audio) / sr * 1000

    return audio, sr, metadata
