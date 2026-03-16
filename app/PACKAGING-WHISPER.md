# PyInstaller Packaging for EchoScribe (Whisper)

## 1. Install Dependencies

Run this from the `app` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-whisper.txt
pip install pyinstaller
```

Build releases from a clean virtual environment that only contains the packages in `requirements-whisper.txt` plus `pyinstaller`. Do not reuse a global Python environment that already has `torch`, `transformers`, or other ML stacks installed, because PyInstaller can accidentally bundle those native runtimes and trigger Windows DLL initialization failures.

## 2. Build the App (One-Folder)

Use the maintained spec file:

```powershell
pyinstaller --clean main.spec
```

The spec intentionally disables UPX for native binaries. Re-enable it only after verifying the packaged app still launches and transcribes correctly on a clean Windows machine.

Output folder:

- `dist/main/`

## 3. Build the Windows Installer (Inno Setup)

Compile `EchoScribeInstaller.iss` with Inno Setup Compiler.

The installer script now packages `dist/main/*` so the full app runtime is included.

## 4. Installer Behavior Notes

- App binaries install under `Program Files`.
- Writable app data is stored under `%LOCALAPPDATA%\EchoScribe`:
  - `%LOCALAPPDATA%\EchoScribe\models`
  - `%LOCALAPPDATA%\EchoScribe\recordings`
- If a model exists in bundled `models/<name>`, the app copies it to user data on first use.

## 5. Shareable Release Checklist

- Build on a clean virtual environment.
- Verify `dist/main/_internal` does not contain `torch/` or `transformers/`.
- Run installer on a clean machine/user profile.
- Verify: launch, microphone capture, transcription, model availability, and uninstall flow.
- If distributing publicly, code-sign both `main.exe` and the installer executable.
