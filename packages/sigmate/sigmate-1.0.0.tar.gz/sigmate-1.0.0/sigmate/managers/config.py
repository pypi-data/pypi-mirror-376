import json
import click
from pathlib import Path
from typing import Dict, Any, Optional

from sigmate.config import DEFAULT_CONFIG_FILE, DEFAULT_KEYRING_DIR


class ConfigManager:
    """Manages loading, accessing, and saving the user's configuration."""

    def __init__(self, config_path: Path = DEFAULT_CONFIG_FILE):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """
        Loads the configuration file if it exists.
        If the file is corrupt, it prints a warning and proceeds with defaults.
        """
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if self.config_path.is_file():
            try:
                self.config = json.loads(self.config_path.read_text("utf-8"))
            except (json.JSONDecodeError, IOError):
                click.secho(
                    f"⚠️  Warning: Configuration file at {self.config_path} is corrupt or unreadable.",
                    fg="yellow",
                    err=True,
                )
                click.secho(
                    f"   Using default values for this session. Run 'sigmate configure' to create a new valid configuration.",
                    fg="yellow",
                    err=True,
                )
                self.config = {}

        if "keyring_path" not in self.config:
            self.config["keyring_path"] = str(DEFAULT_KEYRING_DIR)

    def save(self) -> None:
        """Saves the current configuration to the file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.config_path.write_text(json.dumps(self.config, indent=2), "utf-8")
        except IOError as e:
            raise IOError(
                f"Failed to save configuration to {self.config_path}: {e}"
            ) from e

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """Gets a value from the configuration."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Sets a value in the configuration."""
        self.config[key] = value

    def get_keyring_path(self) -> Path:
        """Gets the path to the public key keyring."""
        keyring_path = Path(self.get("keyring_path", str(DEFAULT_KEYRING_DIR)))
        keyring_path.mkdir(parents=True, exist_ok=True)
        return keyring_path
