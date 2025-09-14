import click

_logger_instance = None

DEFAULT_PREFIXES = {
    "info": "ℹ️",
    "warn": "⚠️",
    "error": "❌",
    "success": "✅",
    "debug": "🐛",
}

FALLBACK_PREFIXES = {
    "info": "[INFO]",
    "warn": "[WARN]",
    "error": "[ERROR]",
    "success": "[OK]",
    "debug": "[DEBUG]",
}


class Logger:
    def __init__(
        self, enabled: bool = False, emojis: bool = True, prefixes: dict = None
    ):
        self.enabled = enabled  # controls debug only
        self.emojis = emojis
        self.prefixes = prefixes or DEFAULT_PREFIXES

    def _emit(self, level: str, message: str, emoji: str = None):
        if level == "debug" and not self.enabled:
            return
        prefix = emoji if self.emojis else FALLBACK_PREFIXES[level]
        click.echo(f"{prefix} {message}")

    def info(self, msg: str, emoji: str = None):
        self._emit("info", msg, emoji)

    def warn(self, msg: str, emoji: str = None):
        self._emit("warn", msg, emoji)

    def error(self, msg: str, emoji: str = None):
        self._emit("error", msg, emoji)

    def success(self, msg: str, emoji: str = None):
        self._emit("success", msg, emoji)

    def debug(self, msg: str, emoji: str = None):
        self._emit("debug", msg, emoji)


def init_logger(enabled: bool = False, emojis: bool = True, prefixes: dict = None):
    global _logger_instance
    _logger_instance = Logger(enabled=enabled, emojis=emojis, prefixes=prefixes)


def get_logger() -> Logger:
    if _logger_instance is None:
        return Logger(enabled=False)
    return _logger_instance
