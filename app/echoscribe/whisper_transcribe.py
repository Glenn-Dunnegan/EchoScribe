def transcribe_wav_whisper(wav_path: str, model_id: str = "base", device: str = "cpu") -> str:
    """
    Transcribe a WAV file using faster-whisper.
    Args:
        wav_path: Path to the WAV file.
        model_id: Whisper model size or a local model path.
        device: 'cpu' or 'cuda'.
    Returns:
        The transcribed text.
    """
    try:
        from faster_whisper import WhisperModel
    except OSError as exc:
        error_code = getattr(exc, "winerror", None)
        if error_code == 1114:
            raise RuntimeError(
                "Failed to initialize the Whisper runtime DLLs. Rebuild the installer from a clean virtual environment using the updated PyInstaller spec so duplicate native runtimes are not bundled."
            ) from exc
        raise RuntimeError(f"Failed to load the Whisper runtime: {exc}") from exc

    model = WhisperModel(model_id, device=device)
    segments, info = model.transcribe(wav_path)
    return "".join([segment.text for segment in segments]).strip()
