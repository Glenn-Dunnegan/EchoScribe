# PyInstaller Packaging for EchoScribe (Whisper)

## 1. Install Dependencies

Run this from the `app` directory:

```powershell
pip install -r requirements-whisper.txt
pip install pyinstaller
```

## 2. Build the App (One-Folder)

Use the maintained spec file:

```powershell
pyinstaller --clean main.spec
```

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
- Run installer on a clean machine/user profile.
- Verify: launch, microphone capture, transcription, model availability, and uninstall flow.
- If distributing publicly, code-sign both `main.exe` and the installer executable.
