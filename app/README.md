
# EchoScribe

EchoScribe is a fully local, offline desktop voice-to-text app.  
It uses free open-source packages and does not call any paid cloud APIs.  
Now powered exclusively by Whisper (faster-whisper) for high-quality, offline transcription with punctuation and corrections.

## What it does

- Records microphone audio from your PC
- Runs local speech recognition with Whisper (faster-whisper)
- Shows transcript in a desktop window
- Lets you copy transcript text
- Supports both Live Streaming and Push-to-Talk modes
- Supports configurable Push-to-Talk keyboard hotkeys (minimum 2-key combo, for example ctrl+alt)
- Shows a visual mic status badge (Idle vs Listening)
- Shows live recording duration while listening is active
- Can type final transcript into the currently focused text field in another app

## Requirements

- Python 3.10+
- Windows microphone permissions enabled for desktop apps
- No internet required after first model download

## Setup

```powershell
cd app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-whisper.txt
```

## Run

```powershell
python main.py
```

## First use

1. Launch the app
2. Select your preferred Whisper model size ("tiny" is fastest, "base" and up are more accurate)
3. Select Record Transcription Mode:
   - Live Streaming: click Start Live Streaming and watch text appear as you speak
   - Push-to-Talk: hold Hold to Talk while speaking, then release to auto-transcribe
4. Optional for Push-to-Talk: enable global hotkey, set a 2+ key combo (for example ctrl+alt), and click Apply
5. Use Copy Text if you want the transcript in your clipboard
6. To write outside EchoScribe:
   - Enable Auto-type final transcript into focused app and use Push-to-Talk for hands-free typing into any app

## Notes

- Default model: Whisper "base" (auto-downloaded on first use)
- Audio recordings are stored under recordings/
