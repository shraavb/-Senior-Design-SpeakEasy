"""
Acoustic feature extraction for fluency analysis.

Extracts F0 (pitch), intensity, formants, and other prosodic features.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not available - some features disabled")

try:
    import parselmouth
    from parselmouth.praat import call
    PRAAT_AVAILABLE = True
except ImportError:
    PRAAT_AVAILABLE = False
    logger.warning("praat-parselmouth not available - advanced prosody disabled")


@dataclass
class AudioFeatures:
    """Container for extracted audio features."""
    # Basic info
    duration_seconds: float = 0.0
    sample_rate: int = 16000

    # Pitch (F0) features
    pitch_values: np.ndarray = field(default_factory=lambda: np.array([]))
    pitch_mean: float = 0.0
    pitch_std: float = 0.0
    pitch_min: float = 0.0
    pitch_max: float = 0.0
    pitch_range: float = 0.0

    # Intensity features
    intensity_values: np.ndarray = field(default_factory=lambda: np.array([]))
    intensity_mean: float = 0.0
    intensity_std: float = 0.0

    # Timing features
    speaking_rate_syllables_per_sec: float = 0.0
    pause_count: int = 0
    pause_durations: List[float] = field(default_factory=list)
    total_pause_duration: float = 0.0
    speech_ratio: float = 1.0  # ratio of speech to total duration

    # Rhythm features
    pvi: float = 0.0  # Pairwise Variability Index

    # Raw audio
    audio_data: np.ndarray = field(default_factory=lambda: np.array([]))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding numpy arrays)."""
        return {
            "duration_seconds": self.duration_seconds,
            "sample_rate": self.sample_rate,
            "pitch_mean": self.pitch_mean,
            "pitch_std": self.pitch_std,
            "pitch_min": self.pitch_min,
            "pitch_max": self.pitch_max,
            "pitch_range": self.pitch_range,
            "intensity_mean": self.intensity_mean,
            "intensity_std": self.intensity_std,
            "speaking_rate_syllables_per_sec": self.speaking_rate_syllables_per_sec,
            "pause_count": self.pause_count,
            "pause_durations": self.pause_durations,
            "total_pause_duration": self.total_pause_duration,
            "speech_ratio": self.speech_ratio,
            "pvi": self.pvi,
        }


def extract_pitch_librosa(audio: np.ndarray, sr: int) -> Dict[str, Any]:
    """
    Extract pitch features using librosa.

    Args:
        audio: Audio data as numpy array
        sr: Sample rate

    Returns:
        Dictionary with pitch statistics
    """
    if not LIBROSA_AVAILABLE:
        return {"pitch_mean": 0, "pitch_std": 0, "pitch_min": 0, "pitch_max": 0}

    try:
        # Use piptrack for pitch estimation
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)

        # Get pitch values where magnitude is significant
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 50:  # Filter out very low frequencies
                pitch_values.append(pitch)

        if not pitch_values:
            return {"pitch_mean": 0, "pitch_std": 0, "pitch_min": 0, "pitch_max": 0}

        pitch_array = np.array(pitch_values)

        return {
            "pitch_values": pitch_array,
            "pitch_mean": float(np.mean(pitch_array)),
            "pitch_std": float(np.std(pitch_array)),
            "pitch_min": float(np.min(pitch_array)),
            "pitch_max": float(np.max(pitch_array)),
            "pitch_range": float(np.max(pitch_array) - np.min(pitch_array)),
        }

    except Exception as e:
        logger.error(f"Error extracting pitch with librosa: {e}")
        return {"pitch_mean": 0, "pitch_std": 0, "pitch_min": 0, "pitch_max": 0}


def extract_pitch_praat(audio_path: str) -> Dict[str, Any]:
    """
    Extract pitch features using Praat (more accurate).

    Args:
        audio_path: Path to audio file

    Returns:
        Dictionary with pitch statistics
    """
    if not PRAAT_AVAILABLE:
        return {}

    try:
        sound = parselmouth.Sound(audio_path)
        pitch = call(sound, "To Pitch", 0.0, 75, 600)

        pitch_values = pitch.selected_array["frequency"]
        pitch_values = pitch_values[pitch_values != 0]  # Remove unvoiced

        if len(pitch_values) == 0:
            return {}

        return {
            "pitch_values": pitch_values,
            "pitch_mean": float(np.mean(pitch_values)),
            "pitch_std": float(np.std(pitch_values)),
            "pitch_min": float(np.min(pitch_values)),
            "pitch_max": float(np.max(pitch_values)),
            "pitch_range": float(np.max(pitch_values) - np.min(pitch_values)),
        }

    except Exception as e:
        logger.error(f"Error extracting pitch with Praat: {e}")
        return {}


def extract_intensity_praat(audio_path: str) -> Dict[str, Any]:
    """
    Extract intensity features using Praat.

    Args:
        audio_path: Path to audio file

    Returns:
        Dictionary with intensity statistics
    """
    if not PRAAT_AVAILABLE:
        return {}

    try:
        sound = parselmouth.Sound(audio_path)
        intensity = call(sound, "To Intensity", 100, 0, "yes")

        intensity_values = intensity.values[0]
        intensity_values = intensity_values[~np.isnan(intensity_values)]

        if len(intensity_values) == 0:
            return {}

        return {
            "intensity_values": intensity_values,
            "intensity_mean": float(np.mean(intensity_values)),
            "intensity_std": float(np.std(intensity_values)),
        }

    except Exception as e:
        logger.error(f"Error extracting intensity with Praat: {e}")
        return {}


def calculate_pvi(durations: List[float]) -> float:
    """
    Calculate normalized Pairwise Variability Index (nPVI).

    PVI measures rhythm by comparing adjacent syllable/vowel durations.
    Higher values indicate more variable (stress-timed) rhythm.
    Lower values indicate more regular (syllable-timed) rhythm.

    Spanish typically has lower PVI (syllable-timed).

    Args:
        durations: List of syllable or interval durations

    Returns:
        nPVI value (0-100 scale)
    """
    if len(durations) < 2:
        return 0.0

    differences = []
    for i in range(len(durations) - 1):
        d1, d2 = durations[i], durations[i + 1]
        if d1 + d2 > 0:
            diff = abs(d1 - d2) / ((d1 + d2) / 2)
            differences.append(diff)

    if not differences:
        return 0.0

    pvi = 100 * np.mean(differences)
    return float(pvi)


def detect_pauses(
    audio: np.ndarray,
    sr: int,
    min_pause_ms: int = 200,
    threshold_db: float = -40.0,
) -> List[Dict[str, float]]:
    """
    Detect pauses in audio based on energy.

    Args:
        audio: Audio data
        sr: Sample rate
        min_pause_ms: Minimum pause duration to detect
        threshold_db: Energy threshold for silence

    Returns:
        List of pause dictionaries with start, end, duration
    """
    # Convert threshold to amplitude
    threshold = 10 ** (threshold_db / 20)

    # Calculate frame size (10ms frames)
    frame_size = int(sr * 0.01)
    hop_size = frame_size

    # Calculate RMS energy for each frame
    energies = []
    for i in range(0, len(audio) - frame_size, hop_size):
        frame = audio[i:i + frame_size]
        rms = np.sqrt(np.mean(frame ** 2))
        energies.append(rms)

    # Find pause regions
    pauses = []
    in_pause = False
    pause_start = 0

    for i, energy in enumerate(energies):
        time_ms = i * 10  # 10ms per frame

        if energy < threshold and not in_pause:
            pause_start = time_ms
            in_pause = True
        elif energy >= threshold and in_pause:
            pause_end = time_ms
            duration = pause_end - pause_start
            if duration >= min_pause_ms:
                pauses.append({
                    "start_ms": pause_start,
                    "end_ms": pause_end,
                    "duration_ms": duration,
                })
            in_pause = False

    return pauses


def extract_features(audio_path: str) -> AudioFeatures:
    """
    Extract all audio features for fluency analysis.

    Args:
        audio_path: Path to audio file (WAV format preferred)

    Returns:
        AudioFeatures object with all extracted features
    """
    features = AudioFeatures()

    # Load audio
    try:
        if LIBROSA_AVAILABLE:
            audio, sr = librosa.load(audio_path, sr=16000)
        else:
            from .preprocessor import load_audio
            audio, sr = load_audio(audio_path, 16000)
    except Exception as e:
        logger.error(f"Error loading audio: {e}")
        return features

    features.audio_data = audio
    features.sample_rate = sr
    features.duration_seconds = len(audio) / sr

    # Extract pitch - prefer Praat, fallback to librosa
    pitch_data = extract_pitch_praat(audio_path)
    if not pitch_data and LIBROSA_AVAILABLE:
        pitch_data = extract_pitch_librosa(audio, sr)

    if pitch_data:
        features.pitch_values = pitch_data.get("pitch_values", np.array([]))
        features.pitch_mean = pitch_data.get("pitch_mean", 0)
        features.pitch_std = pitch_data.get("pitch_std", 0)
        features.pitch_min = pitch_data.get("pitch_min", 0)
        features.pitch_max = pitch_data.get("pitch_max", 0)
        features.pitch_range = pitch_data.get("pitch_range", 0)

    # Extract intensity
    intensity_data = extract_intensity_praat(audio_path)
    if intensity_data:
        features.intensity_values = intensity_data.get("intensity_values", np.array([]))
        features.intensity_mean = intensity_data.get("intensity_mean", 0)
        features.intensity_std = intensity_data.get("intensity_std", 0)

    # Detect pauses
    pauses = detect_pauses(audio, sr)
    features.pause_count = len(pauses)
    features.pause_durations = [p["duration_ms"] for p in pauses]
    features.total_pause_duration = sum(features.pause_durations)

    # Calculate speech ratio
    total_duration_ms = features.duration_seconds * 1000
    if total_duration_ms > 0:
        features.speech_ratio = 1 - (features.total_pause_duration / total_duration_ms)

    # Calculate PVI from pause durations (simplified)
    if features.pause_durations:
        # Use inter-pause intervals as proxy for syllable durations
        speech_intervals = []
        prev_end = 0
        for pause in pauses:
            interval = pause["start_ms"] - prev_end
            if interval > 0:
                speech_intervals.append(interval)
            prev_end = pause["end_ms"]
        # Add final interval
        final_interval = total_duration_ms - prev_end
        if final_interval > 0:
            speech_intervals.append(final_interval)

        features.pvi = calculate_pvi(speech_intervals)

    logger.info(f"Extracted features: duration={features.duration_seconds:.2f}s, "
                f"pitch_mean={features.pitch_mean:.1f}Hz, pauses={features.pause_count}")

    return features
