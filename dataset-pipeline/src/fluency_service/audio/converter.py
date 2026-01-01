"""
Audio format conversion utilities.

Converts various audio formats (M4A, MP3, OGG) to WAV for processing.
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def convert_to_wav(
    input_path: str,
    output_path: str,
    sample_rate: int = 16000,
    channels: int = 1,
) -> bool:
    """
    Convert audio file to WAV format using FFmpeg.

    Args:
        input_path: Path to input audio file (m4a, mp3, ogg, etc.)
        output_path: Path for output WAV file
        sample_rate: Target sample rate (default: 16kHz for Whisper)
        channels: Number of channels (default: 1 for mono)

    Returns:
        True if conversion successful, False otherwise
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        logger.error(f"Input file not found: {input_path}")
        return False

    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-i", str(input_file),
        "-acodec", "pcm_s16le",  # 16-bit signed little-endian PCM
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-loglevel", "error",
        str(output_file),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg conversion failed: {result.stderr}")
            return False

        if not output_file.exists():
            logger.error("Output file not created")
            return False

        logger.info(f"Converted {input_file.name} to WAV ({sample_rate}Hz, {channels}ch)")
        return True

    except subprocess.TimeoutExpired:
        logger.error("FFmpeg conversion timed out")
        return False
    except FileNotFoundError:
        logger.error("FFmpeg not found. Please install FFmpeg.")
        return False
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return False


def get_audio_info(audio_path: str) -> Optional[dict]:
    """
    Get audio file information using FFprobe.

    Args:
        audio_path: Path to audio file

    Returns:
        Dictionary with duration, sample_rate, channels, codec
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(audio_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            return None

        import json
        data = json.loads(result.stdout)

        # Find audio stream
        audio_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "audio":
                audio_stream = stream
                break

        if not audio_stream:
            return None

        return {
            "duration": float(data.get("format", {}).get("duration", 0)),
            "sample_rate": int(audio_stream.get("sample_rate", 0)),
            "channels": int(audio_stream.get("channels", 0)),
            "codec": audio_stream.get("codec_name", "unknown"),
            "bit_rate": int(data.get("format", {}).get("bit_rate", 0)),
        }

    except Exception as e:
        logger.error(f"Error getting audio info: {e}")
        return None


def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is installed and available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False
