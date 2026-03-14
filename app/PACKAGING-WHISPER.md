# PyInstaller Packaging for EchoScribe (Whisper)

## 1. Ensure All Dependencies Are Installed

```powershell
pip install -r requirements-whisper.txt
```

## 2. Pre-download the Whisper "base" Model (Recommended)

Run the app once to trigger model download, or manually download the model and place it in the `models/base` directory:

```powershell
python main.py
# Or manually download and unzip the model to app/models/base
```

## 3. PyInstaller Command (with Data Files)

Run this from the `app` directory:

```powershell
pyinstaller --onefile --windowed --icon=echoscribe.ico \
  --add-data "models;base" \
  --add-data "recordings;recordings" \
  --hidden-import=faster_whisper \
  --hidden-import=soundfile \
  --hidden-import=numpy \
  --hidden-import=ctranslate2 \
  main.py
```

- `--add-data "models;base"` ensures the Whisper model is bundled (if present).
- Add any other required data folders as needed.
- If you use a virtual environment, you may need to specify the full path to `pyinstaller`.

## 4. Distribute the .exe

- The generated .exe will work offline if the `models/base` folder is bundled.
- If the model is not bundled, the app will attempt to download it on first run (requires internet).

## 5. Troubleshooting

- If you see missing DLL or import errors, add more `--hidden-import` flags for any missing modules.
- For large models, the .exe size will increase. You can distribute the model folder separately if needed.

---

For further help, see the README or ask for packaging troubleshooting tips.
