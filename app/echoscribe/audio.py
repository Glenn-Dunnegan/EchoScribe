import threading
import wave
from pathlib import Path
import sounddevice as sd
import numpy as np
from .config import AUDIO_DTYPE, CHANNELS, RECORDINGS_DIR, SAMPLE_RATE
from datetime import datetime


class Recorder:
    def __init__(self) -> None:
        self._frames: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream: sd.InputStream | None = None
        self.is_recording = False

    def start(self) -> None:
        if self.is_recording:
            return

        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        self._frames = []

        def callback(indata: np.ndarray, _frames: int, _time, status) -> None:
            if status:
                return
            with self._lock:
                self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=AUDIO_DTYPE,
            callback=callback,
        )
        self._stream.start()
        self.is_recording = True

    def stop(self) -> Path:
        if not self.is_recording or self._stream is None:
            raise RuntimeError("No active recording to stop.")

        self._stream.stop()
        self._stream.close()
        self._stream = None
        self.is_recording = False

        with self._lock:
            if not self._frames:
                raise RuntimeError("No audio captured.")
            audio = np.concatenate(self._frames, axis=0)

        filename = datetime.now().strftime("recording_%Y%m%d_%H%M%S.wav")
        output_path = RECORDINGS_DIR / filename

        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(np.dtype(AUDIO_DTYPE).itemsize)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio.tobytes())

        return output_path
