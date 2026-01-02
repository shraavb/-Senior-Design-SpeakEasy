"""
Configuration for the Fluency Evaluation Service.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class WhisperConfig:
    """Configuration for Whisper ASR."""
    model_size: str = "base"  # tiny, base, small, medium, large
    device: str = "cpu"  # cpu, cuda
    compute_type: str = "int8"  # float16, int8
    language: str = "es"  # Spanish


@dataclass
class AudioConfig:
    """Configuration for audio processing."""
    sample_rate: int = 16000
    channels: int = 1
    format: str = "wav"
    normalize: bool = True
    vad_aggressiveness: int = 2  # 0-3, higher = more aggressive


@dataclass
class AnalyzerWeights:
    """Weights for composite fluency score calculation."""
    pronunciation: float = 0.25
    temporal: float = 0.20
    lexical: float = 0.15
    disfluency: float = 0.20
    prosodic: float = 0.10
    communicative: float = 0.10

    def validate(self) -> bool:
        """Ensure weights sum to 1.0."""
        total = (
            self.pronunciation + self.temporal + self.lexical +
            self.disfluency + self.prosodic + self.communicative
        )
        return abs(total - 1.0) < 0.001


@dataclass
class CEFRThresholds:
    """Score thresholds for CEFR level assessments."""
    native_like: int = 90      # 90-100
    proficient: int = 75       # 75-89
    developing: int = 60       # 60-74
    needs_work: int = 0        # 0-59

    def get_assessment(self, score: float) -> str:
        """Get assessment label for a score."""
        if score >= self.native_like:
            return "Native-like"
        elif score >= self.proficient:
            return "Proficient"
        elif score >= self.developing:
            return "Developing"
        else:
            return "Needs work"


@dataclass
class ServiceConfig:
    """Main configuration for the Fluency Evaluation Service."""
    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    eval_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "eval")
    temp_dir: Path = field(default_factory=lambda: Path("/tmp/fluency_service"))

    # Sub-configs
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    weights: AnalyzerWeights = field(default_factory=AnalyzerWeights)
    thresholds: CEFRThresholds = field(default_factory=CEFRThresholds)

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    cors_origins: list = field(default_factory=lambda: ["*"])
    max_audio_size_mb: int = 10
    request_timeout_seconds: int = 30

    # Performance
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    max_concurrent_requests: int = 10

    def __post_init__(self):
        """Create temp directory if needed."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "ServiceConfig":
        """Create config from environment variables."""
        config = cls()

        # Override from environment
        if os.getenv("WHISPER_MODEL"):
            config.whisper.model_size = os.getenv("WHISPER_MODEL")
        if os.getenv("WHISPER_DEVICE"):
            config.whisper.device = os.getenv("WHISPER_DEVICE")
        if os.getenv("API_HOST"):
            config.api_host = os.getenv("API_HOST")
        # Support both API_PORT and PORT (Render uses PORT)
        if os.getenv("PORT"):
            config.api_port = int(os.getenv("PORT"))
        elif os.getenv("API_PORT"):
            config.api_port = int(os.getenv("API_PORT"))

        return config


# Default configuration instance
default_config = ServiceConfig()


# Catalan expressions for evaluation (from existing metrics.py)
CATALAN_EXPRESSIONS = {
    "greetings": ["ei", "apa", "home", "buenas", "bon dia", "bona tarda"],
    "farewells": ["apa", "adeu", "a reveure", "fins ara", "passi-ho be"],
    "family": ["nena", "nen", "avi", "iaia", "mama", "papa"],
    "emotions": ["flipar", "molar", "estar rallat", "ostres", "collons"],
    "plans": ["apa va", "va", "fem", "anem", "vinga"],
    "requests": ["si us plau", "home", "escolta", "mira", "escolti"],
}

# Spanish slang markers
SPANISH_SLANG = {
    "common": ["tio", "tia", "mola", "guay", "curro", "pasta", "flipar", "vale"],
    "intensifiers": ["hostia", "joder", "cono", "ostras"],
    "fillers": ["pues", "bueno", "hombre", "mujer", "vamos"],
}

# Discourse markers for communicative competence
DISCOURSE_MARKERS = {
    "connectors": ["bueno", "pues", "entonces", "asi que", "por eso"],
    "hedges": ["creo que", "me parece", "digamos", "en cierto modo"],
    "emphatics": ["la verdad", "en serio", "de verdad", "sin duda"],
    "turn_taking": ["mira", "oye", "escucha", "sabes"],
}

# Filled pauses for disfluency detection
FILLED_PAUSES = {
    "spanish": ["eh", "um", "ah", "este", "esto", "pues", "bueno"],
    "catalan": ["eh", "mmm", "doncs", "o sigui"],
}
