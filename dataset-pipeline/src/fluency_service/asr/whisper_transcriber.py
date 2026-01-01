"""
Whisper-based speech recognition with word-level timestamps.

Supports both OpenAI Whisper and faster-whisper for improved performance.
"""

import logging
from pathlib import Path
from typing import List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Try to import Whisper variants
FASTER_WHISPER_AVAILABLE = False
OPENAI_WHISPER_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
    logger.info("Using faster-whisper for ASR")
except ImportError:
    pass

if not FASTER_WHISPER_AVAILABLE:
    try:
        import whisper
        OPENAI_WHISPER_AVAILABLE = True
        logger.info("Using openai-whisper for ASR")
    except ImportError:
        pass


@dataclass
class WordInfo:
    """Word with timing and confidence information."""
    word: str
    start: float  # seconds
    end: float    # seconds
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "word": self.word,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
        }


@dataclass
class TranscriptResult:
    """Complete transcription result."""
    text: str
    words: List[dict] = field(default_factory=list)
    language: str = "es"
    duration: float = 0.0
    confidence: float = 1.0

    @property
    def word_count(self) -> int:
        return len(self.words)


class WhisperTranscriber:
    """
    Whisper-based transcriber with word-level timestamps.

    Automatically uses faster-whisper if available for better performance,
    otherwise falls back to openai-whisper.
    """

    def __init__(self, config: Optional[Any] = None):
        """
        Initialize the transcriber.

        Args:
            config: WhisperConfig object with model settings
        """
        self.model = None
        self.model_size = config.model_size if config else "base"
        self.device = config.device if config else "cpu"
        self.compute_type = config.compute_type if config else "int8"
        self.language = config.language if config else "es"

        self._load_model()

    def _load_model(self):
        """Load the Whisper model."""
        if FASTER_WHISPER_AVAILABLE:
            logger.info(f"Loading faster-whisper model: {self.model_size}")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            self._use_faster = True

        elif OPENAI_WHISPER_AVAILABLE:
            logger.info(f"Loading openai-whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size, device=self.device)
            self._use_faster = False

        else:
            raise ImportError(
                "No Whisper implementation available. "
                "Install with: pip install faster-whisper or pip install openai-whisper"
            )

    def transcribe(self, audio_path: str) -> TranscriptResult:
        """
        Transcribe audio file with word-level timestamps.

        Args:
            audio_path: Path to audio file (WAV format preferred)

        Returns:
            TranscriptResult with text and word timings
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if self._use_faster:
            return self._transcribe_faster_whisper(audio_path)
        else:
            return self._transcribe_openai_whisper(audio_path)

    def _transcribe_faster_whisper(self, audio_path: str) -> TranscriptResult:
        """Transcribe using faster-whisper."""
        segments, info = self.model.transcribe(
            audio_path,
            language=self.language,
            word_timestamps=True,
            vad_filter=True,
        )

        # Collect all segments and words
        all_text = []
        all_words = []

        for segment in segments:
            all_text.append(segment.text)

            if segment.words:
                for word in segment.words:
                    all_words.append({
                        "word": word.word.strip(),
                        "start": word.start,
                        "end": word.end,
                        "confidence": word.probability if hasattr(word, "probability") else 1.0,
                    })

        text = " ".join(all_text).strip()
        duration = all_words[-1]["end"] if all_words else 0.0

        return TranscriptResult(
            text=text,
            words=all_words,
            language=info.language if hasattr(info, "language") else self.language,
            duration=duration,
            confidence=info.language_probability if hasattr(info, "language_probability") else 1.0,
        )

    def _transcribe_openai_whisper(self, audio_path: str) -> TranscriptResult:
        """Transcribe using openai-whisper."""
        result = self.model.transcribe(
            audio_path,
            language=self.language,
            word_timestamps=True,
        )

        text = result["text"].strip()
        all_words = []

        # Extract word timings from segments
        for segment in result.get("segments", []):
            for word in segment.get("words", []):
                all_words.append({
                    "word": word["word"].strip(),
                    "start": word["start"],
                    "end": word["end"],
                    "confidence": word.get("probability", 1.0),
                })

        duration = all_words[-1]["end"] if all_words else 0.0

        return TranscriptResult(
            text=text,
            words=all_words,
            language=result.get("language", self.language),
            duration=duration,
        )

    def transcribe_with_alignment(
        self,
        audio_path: str,
        expected_text: Optional[str] = None,
    ) -> TranscriptResult:
        """
        Transcribe audio with optional forced alignment to expected text.

        If expected_text is provided, attempts to align the recognized
        words to the expected text for better accuracy.

        Args:
            audio_path: Path to audio file
            expected_text: Optional expected transcript for alignment

        Returns:
            TranscriptResult with aligned word timings
        """
        result = self.transcribe(audio_path)

        if expected_text:
            # Simple alignment: compare recognized words to expected
            expected_words = expected_text.lower().split()
            recognized_words = result.text.lower().split()

            # If reasonably close, use expected text but keep timings
            if len(recognized_words) > 0:
                from difflib import SequenceMatcher
                similarity = SequenceMatcher(
                    None,
                    " ".join(recognized_words),
                    " ".join(expected_words)
                ).ratio()

                if similarity > 0.7:
                    # Use expected text with recognized timings
                    result.text = expected_text

        return result


# Singleton instance for reuse
_transcriber_instance: Optional[WhisperTranscriber] = None


def get_transcriber(config: Optional[Any] = None) -> WhisperTranscriber:
    """Get or create singleton transcriber instance."""
    global _transcriber_instance
    if _transcriber_instance is None:
        _transcriber_instance = WhisperTranscriber(config)
    return _transcriber_instance
