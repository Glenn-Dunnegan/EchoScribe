from __future__ import annotations
from pathlib import Path

def transcribe_wav(wav_path: Path, model_path: Path = None) -> str:
    from .whisper_transcribe import transcribe_wav_whisper
    # Use model_size from model_path if provided, else default to 'base'
    model_size = "base"
    if model_path is not None:
        # Try to extract model size from the model_path (e.g., .../base, .../small)
        model_size = Path(model_path).name
    return transcribe_wav_whisper(str(wav_path), model_size=model_size, device="cpu")
