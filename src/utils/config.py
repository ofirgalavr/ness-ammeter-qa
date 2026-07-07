import yaml
from typing import Dict
import os


def load_config(config_path: str) -> Dict:
    """
    Load configuration file from config.yaml and return as a dictionary.
    For one-off loads with a custom path.
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


# ── Singleton ─────────────────────────────────────────────────────
# Loaded once at module import time — Python caches modules in sys.modules,
# so this object is created exactly once per process regardless of how many
# times get_config() is called.
_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "config.yaml"
)

try:
    _CONFIG: Dict = load_config(_DEFAULT_CONFIG_PATH)
except FileNotFoundError:
    raise FileNotFoundError(
        f"config.yaml not found at {_DEFAULT_CONFIG_PATH}. "
        "Make sure you run from the project root."
    ) from None


def get_config() -> Dict:
    """
    Return the singleton config instance.
    No file I/O after first import — always returns the same object.
    """
    return _CONFIG
