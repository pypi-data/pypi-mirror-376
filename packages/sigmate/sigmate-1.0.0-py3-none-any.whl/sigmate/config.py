import importlib.metadata
from pathlib import Path

try:
    SIGMATE_VERSION = importlib.metadata.version("sigmate")
except importlib.metadata.PackageNotFoundError:
    SIGMATE_VERSION = "0.0.0-dev"

# --- Centralized Paths ---
APP_DIR_NAME = "sigmate"
APP_CONFIG_DIR = Path.home() / ".config" / APP_DIR_NAME
TRUSTED_KEYS_FILENAME = APP_CONFIG_DIR / "trusted_public_keys.json"
DEFAULT_KEYRING_DIR = APP_CONFIG_DIR / "public_keys"
DEFAULT_CONFIG_FILE = APP_CONFIG_DIR / "config.json"
# --- End Centralized Paths ---

DEFAULT_EXCLUDED_EXTENSIONS = {".sig", ".sigmeta.json"}
SIGNATURES_FOLDER = "signatures"
