import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
APP_DATA_ROOT = Path(os.getenv("LOCALAPPDATA", APP_ROOT)) / "EchoScribe"
BUNDLED_MODELS_DIR = APP_ROOT / "models"
MODELS_DIR = APP_DATA_ROOT / "models"
RECORDINGS_DIR = APP_DATA_ROOT / "recordings"

SAMPLE_RATE = 16000
CHANNELS = 1
AUDIO_DTYPE = "int16"
DEFAULT_MODEL_NAME = "base"
MODEL_DOWNLOAD_BASE = "https://huggingface.co/guillaumekln/faster-whisper-large-v2/resolve/main"  # Or your preferred model source
