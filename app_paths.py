"""Writable Linux/Windows application paths."""

import os
import sys
from pathlib import Path

APP_NAME = "quaege-bot"

if os.name == "nt":
    CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "Quaege Bot"
    DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Quaege Bot"
else:
    CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME
    DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / APP_NAME

EXPORT_DIR = DATA_DIR / "exports"
USER_CONFIG_PATH = CONFIG_DIR / "config.py"
SETTINGS_PATH = CONFIG_DIR / "settings.json"


def ensure_directories():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def path_from_environment(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value).expanduser() if value else default
