from __future__ import annotations
from pathlib import Path

def transcribe_wav(wav_path: Path, model_path: Path | None = None) -> str:
    from .whisper_transcribe import transcribe_wav_whisper

    model_id = str(model_path) if model_path is not None else "base"
    return transcribe_wav_whisper(str(wav_path), model_id=model_id, device="cpu")
