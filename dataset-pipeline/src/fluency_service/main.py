"""
FastAPI entry point for the Fluency Evaluation Service.

Run with:
    uvicorn src.fluency_service.main:app --host 0.0.0.0 --port 8001 --reload

Or programmatically:
    python -m src.fluency_service.main
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import router
from .config import default_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    # Startup
    logger.info("Starting Fluency Evaluation Service...")
    logger.info(f"Whisper model: {default_config.whisper.model_size}")
    logger.info(f"Device: {default_config.whisper.device}")

    # Pre-load Whisper model for faster first request (optional)
    # Uncomment to enable:
    # from .asr.whisper_transcriber import WhisperTranscriber
    # _ = WhisperTranscriber(default_config.whisper)
    # logger.info("Whisper model pre-loaded")

    yield

    # Shutdown
    logger.info("Shutting down Fluency Evaluation Service...")


# Create FastAPI app
app = FastAPI(
    title="SpeakEasy Fluency Evaluation Service",
    description="""
    Real-time fluency assessment API for the SpeakEasy language learning app.

    ## Features

    - **Pronunciation Accuracy** (25%): Phoneme accuracy, Catalan markers, intonation
    - **Temporal Metrics** (20%): Speaking rate, pause patterns, response latency
    - **Lexical Accuracy** (15%): Word Error Rate, expression usage, completeness
    - **Disfluency Detection** (20%): Filled pauses, repetitions, self-corrections
    - **Prosodic Quality** (10%): Pitch range, rhythm, volume consistency
    - **Communicative Competence** (10%): Register, discourse markers, turn-taking

    ## Quick Start

    ```bash
    curl -X POST "http://localhost:8001/api/v1/fluency/evaluate" \\
         -H "Content-Type: application/json" \\
         -d '{"audio_data": "<base64_audio>", "expected_response": "Hola, nen!"}'
    ```
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=default_config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "SpeakEasy Fluency Evaluation Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/fluency/health",
        "evaluate": "/api/v1/fluency/evaluate",
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.fluency_service.main:app",
        host=default_config.api_host,
        port=default_config.api_port,
        reload=True,
    )
