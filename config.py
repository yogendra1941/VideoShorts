"""Configuration manager for VideoShorts."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent
TEMP_DIR = PROJECT_ROOT / "temp"
OUTPUT_DIR = PROJECT_ROOT / "output"
PLANS_DIR = PROJECT_ROOT / "plans"

# Ensure directories exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

class Config:
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "inception").lower()

    # Inception Labs API (mercury-3)
    INCEPTION_API_KEY: str = os.getenv("INCEPTION_API_KEY", "")
    INCEPTION_BASE_URL: str = os.getenv("INCEPTION_BASE_URL", "https://api.inceptionlabs.ai/v1")
    INCEPTION_MODEL: str = os.getenv("INCEPTION_MODEL", "mercury-3")

    # Local Ollama Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Cloud Fallback Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Speech Recognition (faster-whisper)
    ASR_DEVICE: str = os.getenv("ASR_DEVICE", "cuda")
    ASR_MODEL_SIZE: str = os.getenv("ASR_MODEL_SIZE", "small")
    ASR_COMPUTE_TYPE: str = os.getenv("ASR_COMPUTE_TYPE", "float16")
    ASR_CPU_FALLBACK: bool = os.getenv("ASR_CPU_FALLBACK", "true").lower() in ("1", "true", "yes")

    # Video Settings
    TARGET_WIDTH: int = 1080
    TARGET_HEIGHT: int = 1920
    MIN_CLIP_DURATION: int = int(os.getenv("MIN_CLIP_DURATION", "20"))
    MAX_CLIP_DURATION: int = int(os.getenv("MAX_CLIP_DURATION", "60"))
    LOUDNORM_ENABLED: bool = os.getenv("LOUDNORM_ENABLED", "true").lower() in ("1", "true", "yes")

    # Paths & Binaries
    PROJECT_ROOT: Path = PROJECT_ROOT
    TEMP_DIR: Path = TEMP_DIR
    OUTPUT_DIR: Path = OUTPUT_DIR
    FFMPEG_BIN: str = os.getenv("FFMPEG_BIN", "ffmpeg")
    FFPROBE_BIN: str = os.getenv("FFPROBE_BIN", "ffprobe")
    YTDLP_BIN: str = os.getenv("YTDLP_BIN", "yt-dlp")

config = Config()
