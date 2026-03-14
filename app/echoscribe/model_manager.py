
import io
import zipfile
from pathlib import Path

import requests

from .config import DEFAULT_MODEL_NAME, MODELS_DIR, MODEL_DOWNLOAD_BASE


def get_model_path(model_name: str = DEFAULT_MODEL_NAME) -> Path:
    return MODELS_DIR / model_name


def model_exists(model_name: str = DEFAULT_MODEL_NAME) -> bool:
    return get_model_path(model_name).exists()


def download_model(model_name: str = DEFAULT_MODEL_NAME) -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    target_dir = get_model_path(model_name)
    if target_dir.exists():
        return target_dir

    model_url = f"{MODEL_DOWNLOAD_BASE}/{model_name}.zip"
    response = requests.get(model_url, timeout=120)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        zip_ref.extractall(MODELS_DIR)

    if not target_dir.exists():
        found_dirs = [p for p in MODELS_DIR.iterdir() if p.is_dir() and model_name in p.name]
        if len(found_dirs) == 1:
            found_dirs[0].rename(target_dir)

    if not target_dir.exists():
        raise FileNotFoundError(f"Model was downloaded but folder {target_dir} was not found.")

    return target_dir
