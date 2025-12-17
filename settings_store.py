# settings_store.py
# Persistencia simple en JSON para la posición y flags

from pathlib import Path
import json

DEFAULT_FILE = Path.home() / ".nowplaying_overlay.json"

def load_settings(path: Path = DEFAULT_FILE) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}

def save_settings(data: dict, path: Path = DEFAULT_FILE) -> None:
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
