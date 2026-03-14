from faster_whisper import WhisperModel
import numpy as np
import soundfile as sf

def transcribe_wav_whisper(wav_path: str, model_size: str = "base", device: str = "cpu") -> str:
    """
    Transcribe a WAV file using faster-whisper.
    Args:
        wav_path: Path to the WAV file.
        model_size: Whisper model size (e.g., 'base', 'small').
        device: 'cpu' or 'cuda'.
    Returns:
        The transcribed text.
    """
    model = WhisperModel(model_size, device=device)
    segments, info = model.transcribe(wav_path)
    return "".join([segment.text for segment in segments]).strip()
