import fnmatch
from pathlib import Path
from typing import List, Optional, Tuple
from sigmate.utils.logger import Logger


class CustomIgnoreMatcher:
    def __init__(self, start_dir: Path, logger: Optional[Logger] = None):
        self.start_dir: Path = start_dir.resolve()
        self.logger: Optional[Logger] = logger
        self.patterns: List[Tuple[str, bool, bool, Path]] = []
        self._load_ignore_files()

    def _find_and_load_ignore_file(
        self, directory: Path, filename: str = ".sigmateignore"
    ) -> bool:
        ignore_file = directory / filename
        if ignore_file.is_file():
            if self.logger:
                self.logger.debug(
                    f"Loading ignore patterns from: {ignore_file}", emoji="📋"
                )
            with ignore_file.open("r", encoding="utf-8") as f:
                for line_num, line_content in enumerate(f, 1):
                    pattern = line_content.strip()
                    if not pattern or pattern.startswith("#"):
                        continue
                    is_negative = pattern.startswith("!")
                    if is_negative:
                        pattern = pattern[1:]
                    is_dir_only = pattern.endswith("/")
                    if is_dir_only:
                        pattern = pattern[:-1]
                    self.patterns.append((pattern, is_negative, is_dir_only, directory))
            return True
        return False

    def _load_ignore_files(self) -> None:
        current_dir = self.start_dir
        while current_dir != current_dir.parent:
            if self._find_and_load_ignore_file(current_dir, ".sigmateignore"):
                return
            if self._find_and_load_ignore_file(current_dir, ".gitignore"):
                return
            current_dir = current_dir.parent
        if self._find_and_load_ignore_file(current_dir, ".sigmateignore"):
            return
        if self._find_and_load_ignore_file(current_dir, ".gitignore"):
            return

    def matches(self, path_to_check: Path, is_dir: Optional[bool] = None) -> bool:
        if not self.patterns:
            return False

        resolved_path_to_check = path_to_check.resolve()
        if is_dir is None:
            is_dir = resolved_path_to_check.is_dir()

        for (
            pattern_str,
            is_negative_rule,
            is_dir_only_rule,
            ignore_file_base_path,
        ) in reversed(self.patterns):
            if is_dir_only_rule and not is_dir:
                continue

            try:
                relative_path_to_check = resolved_path_to_check.relative_to(
                    ignore_file_base_path
                )
            except ValueError:
                continue

            path_str_for_match = relative_path_to_check.as_posix()

            does_match = False
            if "/" not in pattern_str:
                if fnmatch.fnmatch(resolved_path_to_check.name, pattern_str):
                    does_match = True
            else:
                if fnmatch.fnmatch(path_str_for_match, pattern_str.lstrip("/")):
                    does_match = True
                elif is_dir and fnmatch.fnmatch(
                    path_str_for_match + "/", pattern_str.lstrip("/")
                ):
                    does_match = True

            if does_match:
                if is_negative_rule:
                    return False
                else:
                    return True

        return False
