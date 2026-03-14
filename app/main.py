from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from time import perf_counter, sleep
from pathlib import Path
from tkinter import messagebox, ttk


import pyautogui
import sounddevice as sd
from pynput import keyboard as pynput_keyboard

from echoscribe.audio import Recorder
from echoscribe.config import AUDIO_DTYPE, CHANNELS, DEFAULT_MODEL_NAME, SAMPLE_RATE
from echoscribe.model_manager import download_model, get_model_path, model_exists
from echoscribe.transcribe import transcribe_wav


class EchoScribeApp:
    def _stop_timer(self) -> None:
        if self._timer_job is not None:
            self.root.after_cancel(self._timer_job)
            self._timer_job = None
        self._recording_started_at = None
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("EchoScribe - Offline Voice to Text")
        self.root.geometry("800x520")

        self.recorder = Recorder()
        self.last_recording: Path | None = None
        self.whisper_model_size = tk.StringVar(value="base")  # Whisper model size dropdown
        self.record_mode = tk.StringVar(value="ptt")  # Default to Push-to-Talk mode
        self.status = tk.StringVar(value="Ready")
        self.mic_state = tk.StringVar(value="Mic: Idle")
        self.record_timer = tk.StringVar(value="00:00")
        self.control_hint = tk.StringVar(value="Current Controls: Hold to Talk button OR hold hotkey (ctrl+alt). Release to transcribe.")
        self.auto_type_to_focused = tk.BooleanVar(value=True)  # Enable auto-type by default
        self.ptt_hotkey_enabled = tk.BooleanVar(value=True)    # Enable global hotkey by default
        self.keep_recordings = tk.BooleanVar(value=False)      # Default: do not keep recordings
        self.ptt_hotkey = tk.StringVar(value="ctrl+win")
        self.last_transcript = ""
        self._recording_started_at: float | None = None
        self._timer_job: str | None = None
        self._live_stream: sd.RawInputStream | None = None
        self._live_queue: queue.Queue[bytes] = queue.Queue()
        self._live_stop_event = threading.Event()
        self._live_thread: threading.Thread | None = None
        self._live_chunks: list[str] = []
        self._hotkey_listener: pynput_keyboard.Listener | None = None
        self._hotkey_combo_tokens: set[str] = {"lshift"}
        self._pressed_tokens: set[str] = set()
        self._hotkey_active = False
        self._key_debug = tk.StringVar(value="Key Debug: []")
        self._runtime_mode = "live"
        self._runtime_hotkey_enabled = False

        self._build_ui()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill=tk.BOTH, expand=True)

        ttk.Label(outer, text="EchoScribe", font=("Segoe UI", 20, "bold")).pack(anchor=tk.W)
        ttk.Label(
            outer,
            text="Local speech-to-text with no paid APIs or subscriptions.",
            font=("Segoe UI", 10),
        ).pack(anchor=tk.W, pady=(0, 10))

        model_row = ttk.Frame(outer)
        model_row.pack(fill=tk.X, pady=(8, 8))
        ttk.Label(model_row, text="Whisper Model Size:").pack(side=tk.LEFT)
        whisper_size_dropdown = ttk.Combobox(model_row, textvariable=self.whisper_model_size, state="readonly", width=8)
        whisper_size_dropdown['values'] = ("tiny", "base", "small", "medium", "large")
        whisper_size_dropdown.pack(side=tk.LEFT, padx=8)
        # No engine dropdown or backend logic needed; only Whisper is supported

        mode_row = ttk.Frame(outer)
        mode_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(mode_row, text="Record Transcription Mode:").pack(side=tk.LEFT)
        ttk.Radiobutton(
            mode_row,
            text="Live Streaming",
            value="live",
            variable=self.record_mode,
            command=self._on_mode_change,
        ).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Radiobutton(
            mode_row,
            text="Push-to-Talk",
            value="ptt",
            variable=self.record_mode,
            command=self._on_mode_change,
        ).pack(side=tk.LEFT, padx=(8, 0))

        hotkey_row = ttk.Frame(outer)
        hotkey_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Checkbutton(
            hotkey_row,
            text="Enable global Push-to-Talk hotkey (2+ keys)",
            variable=self.ptt_hotkey_enabled,
            command=self._on_hotkey_settings_change,
        ).pack(side=tk.LEFT)
        ttk.Label(hotkey_row, text="Hotkey:").pack(side=tk.LEFT, padx=(10, 4))
        ttk.Entry(hotkey_row, textvariable=self.ptt_hotkey, width=16).pack(side=tk.LEFT)
        ttk.Button(hotkey_row, text="Apply", command=self.apply_ptt_hotkey).pack(side=tk.LEFT, padx=(8, 0))

        hint_row = ttk.Frame(outer)
        hint_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(hint_row, textvariable=self.control_hint, foreground="#0f4c81").pack(anchor=tk.W)

        debug_row = ttk.Frame(outer)
        debug_row.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(debug_row, textvariable=self._key_debug, foreground="#b22222").pack(anchor=tk.W)

        actions = ttk.Frame(outer)
        actions.pack(fill=tk.X, pady=8)
        self.record_button = ttk.Button(actions, text="Start Recording", command=self.toggle_recording)
        self.record_button.pack(side=tk.LEFT)
        ttk.Button(actions, text="Transcribe Last Recording", command=self.transcribe_last_recording).pack(side=tk.LEFT, padx=8)
        ttk.Button(actions, text="Copy Text", command=self.copy_text).pack(side=tk.LEFT)

        output_row = ttk.Frame(outer)
        output_row.pack(fill=tk.X, pady=(0, 4))
        ttk.Checkbutton(
            output_row,
            text="Auto-type final transcript into focused app",
            variable=self.auto_type_to_focused,
        ).pack(side=tk.LEFT)

        ttk.Checkbutton(
            output_row,
            text="Keep recordings after transcription",
            variable=self.keep_recordings,
        ).pack(side=tk.LEFT, padx=(16, 0))

        mic_row = ttk.Frame(outer)
        mic_row.pack(fill=tk.X, pady=(2, 4))
        ttk.Label(mic_row, text="Input Status:").pack(side=tk.LEFT)
        self.mic_indicator = tk.Label(
            mic_row,
            textvariable=self.mic_state,
            fg="#ffffff",
            bg="#2f855a",
            padx=10,
            pady=4,
            font=("Segoe UI", 9, "bold"),
        )
        self.mic_indicator.pack(side=tk.LEFT, padx=8)
        ttk.Label(mic_row, text="Duration:").pack(side=tk.LEFT, padx=(10, 2))
        ttk.Label(mic_row, textvariable=self.record_timer, font=("Consolas", 10, "bold")).pack(side=tk.LEFT)

        self._on_mode_change()
        self.apply_ptt_hotkey(show_success=False)

        ttk.Label(outer, textvariable=self.status, foreground="#0f4c81").pack(anchor=tk.W, pady=(6, 8))

        self.text_box = tk.Text(outer, wrap=tk.WORD, font=("Consolas", 11))
        self.text_box.pack(fill=tk.BOTH, expand=True)

    def set_status(self, message: str) -> None:
        self.status.set(message)

    def _set_recording_indicator(self, is_recording: bool) -> None:
        if is_recording:
            self.mic_state.set("Mic: Listening")
            self.mic_indicator.config(bg="#c53030")
            return

        self.mic_state.set("Mic: Idle")
        self.mic_indicator.config(bg="#2f855a")

    def _start_timer(self) -> None:
        self._recording_started_at = perf_counter()
        self.record_timer.set("00:00")
        self._schedule_timer_tick()

    def _schedule_timer_tick(self) -> None:
        if self._recording_started_at is None:
            return

        elapsed_seconds = int(perf_counter() - self._recording_started_at)
        minutes, seconds = divmod(elapsed_seconds, 60)
        self.record_timer.set(f"{minutes:02d}:{seconds:02d}")
        self._timer_job = self.root.after(250, self._schedule_timer_tick)

    def download_model(self) -> None:
        def worker() -> None:
            model_name = self.model_name.get().strip()
            if not model_name:
                self.root.after(0, lambda: messagebox.showerror("Error", "Model name cannot be empty."))
                return

            self.root.after(0, lambda: self.set_status(f"Downloading {model_name}..."))
            try:
                download_model(model_name)
                self.root.after(0, lambda: self.set_status(f"Model ready: {model_name}"))
            except Exception as exc:
                self.root.after(0, lambda: self.set_status("Model download failed"))
                self.root.after(0, lambda: messagebox.showerror("Download error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _normalize_hotkey_token(self, token: str) -> str | None:
        cleaned = token.strip().lower().replace(" ", "")
        aliases = {
            "control": "ctrl",
            "leftctrl": "lctrl",
            "rightctrl": "rctrl",
            "leftalt": "lalt",
            "rightalt": "ralt",
            "leftshift": "lshift",
            "rightshift": "rshift",
            "windows": "win",
            "winkey": "win",
            "command": "win",
            "leftwin": "lwin",
            "rightwin": "rwin",
        }
        normalized = aliases.get(cleaned, cleaned)

        allowed = {
            "ctrl",
            "alt",
            "shift",
            "lctrl",
            "rctrl",
            "lalt",
            "ralt",
            "lshift",
            "rshift",
            "win",
            "lwin",
            "rwin",
        }
        if len(normalized) == 1 and normalized.isalnum():
            return normalized
        if normalized in allowed:
            return normalized
        return None

    def _tokenize_hotkey_config(self, value: str) -> set[str]:
        parts = [p for p in value.split("+") if p.strip()]
        if not parts:
            raise ValueError("Hotkey cannot be empty.")

        tokens: set[str] = set()

        for part in parts:
            token = self._normalize_hotkey_token(part)
            if token is None:
                raise ValueError(f"Unsupported hotkey part: {part}")
            # Windows key is now allowed
            tokens.add(token)

        if len(tokens) < 2:
            raise ValueError("Use at least a 2-key combo for Push-to-Talk hotkey (for example ctrl+win).")
        return tokens

    def _tokens_for_pressed_key(self, key) -> set[str]:
        if isinstance(key, pynput_keyboard.KeyCode):
            if key.char:
                return {key.char.lower()}
            return set()

        key_map = {
            pynput_keyboard.Key.ctrl: {"ctrl"},
            pynput_keyboard.Key.ctrl_l: {"ctrl", "lctrl"},
            pynput_keyboard.Key.ctrl_r: {"ctrl", "rctrl"},
            pynput_keyboard.Key.alt: {"alt"},
            pynput_keyboard.Key.alt_l: {"alt", "lalt"},
            pynput_keyboard.Key.alt_r: {"alt", "ralt"},
            pynput_keyboard.Key.alt_gr: {"alt", "ralt"},
            pynput_keyboard.Key.shift: {"shift"},
            pynput_keyboard.Key.shift_l: {"shift", "lshift"},
            pynput_keyboard.Key.shift_r: {"shift", "rshift"},
            pynput_keyboard.Key.cmd: {"win"},
            pynput_keyboard.Key.cmd_l: {"win", "lwin"},
            pynput_keyboard.Key.cmd_r: {"win", "rwin"},
        }
        return key_map.get(key, set())

    def _token_is_satisfied(self, token: str) -> bool:
        if token in self._pressed_tokens:
            return True

        equivalents = {
            "lshift": {"shift", "lshift"},
            "rshift": {"shift", "rshift"},
            "lctrl": {"ctrl", "lctrl"},
            "rctrl": {"ctrl", "rctrl"},
            "lalt": {"alt", "lalt"},
            "ralt": {"alt", "ralt"},
            "lwin": {"win", "lwin"},
            "rwin": {"win", "rwin"},
        }
        if token in equivalents:
            return any(candidate in self._pressed_tokens for candidate in equivalents[token])
        return False

    def _combo_is_pressed(self) -> bool:
        return all(self._token_is_satisfied(token) for token in self._hotkey_combo_tokens)

    def _on_hotkey_press(self, key) -> None:
        self._pressed_tokens.update(self._tokens_for_pressed_key(key))

        # Update key debug display
        self.root.after(0, lambda: self._key_debug.set(f"Key Debug: {sorted(self._pressed_tokens)}"))

        if self._runtime_mode != "ptt" or not self._runtime_hotkey_enabled:
            return

        if self._hotkey_active or self.recorder.is_recording:
            return

        if self._combo_is_pressed():
            self._hotkey_active = True
            self.root.after(0, lambda: self._push_to_talk_press(None))

    def _on_hotkey_release(self, key) -> None:
        released = self._tokens_for_pressed_key(key)
        for token in released:
            self._pressed_tokens.discard(token)

        # Update key debug display
        self.root.after(0, lambda: self._key_debug.set(f"Key Debug: {sorted(self._pressed_tokens)}"))

        if not self._hotkey_active:
            return

        if not self._combo_is_pressed():
            self._hotkey_active = False
            self.root.after(0, lambda: self._push_to_talk_release(None))

    def _start_hotkey_listener(self) -> None:
        if self._hotkey_listener is not None:
            return

        self._pressed_tokens.clear()
        self._hotkey_active = False
        self._hotkey_listener = pynput_keyboard.Listener(on_press=self._on_hotkey_press, on_release=self._on_hotkey_release)
        self._hotkey_listener.start()

    def _stop_hotkey_listener(self) -> None:
        if self._hotkey_listener is None:
            return

        self._hotkey_listener.stop()
        self._hotkey_listener = None
        self._pressed_tokens.clear()
        self._hotkey_active = False

    def _refresh_hotkey_listener(self) -> None:
        should_run = self._runtime_mode == "ptt" and self._runtime_hotkey_enabled
        if should_run:
            self._start_hotkey_listener()
            return
        self._stop_hotkey_listener()

    def _sync_runtime_hotkey_state(self) -> None:
        self._runtime_mode = self.record_mode.get()
        self._runtime_hotkey_enabled = self.ptt_hotkey_enabled.get()

    def apply_ptt_hotkey(self, show_success: bool = True) -> None:
        try:
            self._hotkey_combo_tokens = self._tokenize_hotkey_config(self.ptt_hotkey.get())
        except ValueError as exc:
            messagebox.showerror("Hotkey error", str(exc))
            return

        self._sync_runtime_hotkey_state()
        self._refresh_hotkey_listener()
        if show_success:
            combo_text = "+".join(part.strip() for part in self.ptt_hotkey.get().split("+") if part.strip())
            self.set_status(f"Push-to-Talk hotkey set: {combo_text}")

    def _on_hotkey_settings_change(self) -> None:
        self._sync_runtime_hotkey_state()
        self._refresh_hotkey_listener()
        if self.record_mode.get() == "ptt":
            if self.ptt_hotkey_enabled.get():
                combo_text = "+".join(part.strip() for part in self.ptt_hotkey.get().split("+") if part.strip())
                self.control_hint.set(f"Current Controls: Hold to Talk button OR hold hotkey ({combo_text}). Release to transcribe.")
            else:
                self.control_hint.set("Current Controls: Hold to Talk while pressed. Release to transcribe.")

    def _on_mode_change(self) -> None:
        mode = self.record_mode.get()
        self._sync_runtime_hotkey_state()
        self.record_button.unbind("<ButtonPress-1>")
        self.record_button.unbind("<ButtonRelease-1>")

        if mode == "ptt":
            if self._live_stream is not None:
                self._stop_live_streaming()
            self.record_button.config(text="Hold to Talk", command=lambda: None)
            self.record_button.bind("<ButtonPress-1>", self._push_to_talk_press)
            self.record_button.bind("<ButtonRelease-1>", self._push_to_talk_release)
            if self.ptt_hotkey_enabled.get():
                combo_text = "+".join(part.strip() for part in self.ptt_hotkey.get().split("+") if part.strip())
                self.control_hint.set(f"Current Controls: Hold to Talk button OR hold hotkey ({combo_text}). Release to transcribe.")
            else:
                self.control_hint.set("Current Controls: Hold to Talk while pressed. Release to transcribe.")
            self._refresh_hotkey_listener()
            self.set_status("Push-to-Talk mode enabled")
            return

        self.record_button.config(text="Start Live Streaming", command=self.toggle_recording)
        self.control_hint.set("Current Controls: Click Start Live Streaming. Click Stop Live Streaming to finish.")
        self._refresh_hotkey_listener()
        self.set_status("Live Streaming mode enabled")

    def _start_recording(self) -> None:
        self.recorder.start()
        self._set_recording_indicator(True)
        self._start_timer()

    def _stop_recording(self) -> None:
        self.last_recording = self.recorder.stop()
        self._set_recording_indicator(False)
        self._stop_timer()

    def _push_to_talk_press(self, _event) -> None:
        if self.recorder.is_recording:
            return
        try:
            self._start_recording()
            self.set_status("Listening... release to transcribe")
        except Exception as exc:
            messagebox.showerror("Recording error", str(exc))

    def _push_to_talk_release(self, _event) -> None:
        if not self.recorder.is_recording:
            return
        try:
            self._stop_recording()
            self.set_status(f"Saved: {self.last_recording}")
            self.transcribe_last_recording()
        except Exception as exc:
            messagebox.showerror("Recording error", str(exc))


    def _start_live_streaming(self) -> None:
        if self._live_stream is not None:
            return

        model_name = self.model_name.get().strip()
        model_path = get_model_path(model_name)
        if not model_exists(model_name):
            messagebox.showwarning("Missing model", f"Download model first: {model_name}")
            return

        self._live_chunks = []
        self._live_queue = queue.Queue()
        self._live_stop_event.clear()

        def callback(indata, _frames, _time, status) -> None:
            if status:
                return
            self._live_queue.put(bytes(indata))

        self._live_stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=AUDIO_DTYPE,
            callback=callback,
        )
        self._live_stream.start()
        self._set_recording_indicator(True)
        self._start_timer()
        self.record_button.config(text="Stop Live Streaming")
        self.control_hint.set("Current Controls: Live streaming active. Click Stop Live Streaming to end.")
        self.set_status("Streaming transcription... speak now")
        self._show_transcript("(Listening...)")

        self._live_thread = threading.Thread(target=self._streaming_worker, args=(model_path,), daemon=True)
        self._live_thread.start()

    def _stop_live_streaming(self) -> None:
        if self._live_stream is None:
            return

        stream = self._live_stream
        self._live_stream = None
        stream.stop()
        stream.close()
        self._live_stop_event.set()
        self._set_recording_indicator(False)
        self._stop_timer()
        self.record_button.config(text="Start Live Streaming")
        self.control_hint.set("Current Controls: Click Start Live Streaming. Click Stop Live Streaming to finish.")

    def toggle_recording(self) -> None:
        if self.record_mode.get() != "live":
            return

        if self._live_stream is None:
            try:
                self._start_live_streaming()
            except Exception as exc:
                messagebox.showerror("Recording error", str(exc))
            return

        try:
            self._stop_live_streaming()
        except Exception as exc:
            messagebox.showerror("Recording error", str(exc))

    def transcribe_last_recording(self) -> None:
        if not self.last_recording:
            messagebox.showwarning("No recording", "Record audio first.")
            return


        whisper_size = self.whisper_model_size.get()
        keep_recordings = self.keep_recordings.get()
        last_recording_path = self.last_recording
        def worker() -> None:
            self.root.after(0, lambda: self.set_status("Transcribing..."))
            try:
                from echoscribe.whisper_transcribe import transcribe_wav_whisper
                transcript = transcribe_wav_whisper(str(last_recording_path), model_size=whisper_size, device="cpu")
                # If auto-type is enabled, only type into focused app and skip updating EchoScribe's text box
                if transcript and self.auto_type_to_focused.get():
                    def type_worker():
                        try:
                            pyautogui.write(transcript.strip() + " ", interval=0.002)
                            self.root.after(0, lambda: self.set_status("Transcript typed into focused app"))
                        except Exception as exc:
                            self.root.after(0, lambda: messagebox.showerror("Type error", str(exc)))
                    threading.Thread(target=type_worker, daemon=True).start()
                else:
                    self.root.after(0, lambda: self._show_transcript(transcript))
                    self.root.after(0, lambda: self.set_status("Transcription complete"))
            except Exception as exc:
                self.root.after(0, lambda: self.set_status("Transcription failed"))
                self.root.after(0, lambda: messagebox.showerror("Transcription error", str(exc)))
            finally:
                if not keep_recordings and last_recording_path and last_recording_path.exists():
                    try:
                        last_recording_path.unlink()
                        self.root.after(0, lambda: self.set_status("Recording deleted after transcription"))
                    except Exception as exc:
                        self.root.after(0, lambda: messagebox.showerror("Delete error", f"Could not delete recording: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _show_transcript(self, transcript: str) -> None:
        self.text_box.delete("1.0", tk.END)
        if transcript:
            self.text_box.insert(tk.END, transcript)
            self.last_transcript = transcript
        else:
            self.text_box.insert(tk.END, "(No speech recognized)")
            self.last_transcript = ""

    def type_into_focused_app(self) -> None:
        transcript = self.text_box.get("1.0", tk.END).strip()
        self._queue_type_to_focused_app(transcript, 3.0)

    def copy_text(self) -> None:
        text = self.text_box.get("1.0", tk.END).strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.set_status("Transcript copied to clipboard")


def main() -> None:
    root = tk.Tk()
    app = EchoScribeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
