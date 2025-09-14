import re
from pathlib import Path
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass

from sigmate.utils.logger import Logger


@dataclass
class ParsedChecksumEntry:
    """Represents a single parsed entry from a checksum file."""

    filename: str
    expected_hash: str
    algorithm: Optional[str]
    original_line: str
    line_number: int


ChecksumFileFormat = Literal["gnu", "bsd", "auto"]
SupportedChecksumAlgorithm = Literal["md5", "sha1", "sha256", "sha512"]

# Regex for GNU style: HASH  FILENAME (FILENAME can have spaces)
# The (* or space) for binary/text mode is captured but might not be strictly enforced by this regex.
GNU_LINE_RE = re.compile(r"^(?P<hash>[a-fA-F0-9]+)\s+[\s*]?(?P<filename>.+?)\s*$")

# Regex for BSD style: ALGO (FILENAME) = HASH
BSD_LINE_RE = re.compile(
    r"^(?P<algo>[A-Za-z0-9]+)\s*\((?P<filename>.+?)\)\s*=\s*(?P<hash>[a-fA-F0-9]+)\s*$"
)

SUPPORTED_ALGORITHMS_MAP: Dict[str, SupportedChecksumAlgorithm] = {
    "MD5": "md5",
    "SHA1": "sha1",
    "SHA256": "sha256",
    "SHA384": "sha384",
    "SHA512": "sha512",
}


def get_algo_from_filename(
    checksum_file_path: Path,
) -> Optional[SupportedChecksumAlgorithm]:
    """Infers checksum algorithm from common checksum filenames if possible."""
    name = checksum_file_path.name.upper()
    if "MD5SUM" in name or name.endswith(".MD5"):
        return "md5"
    if "SHA1SUM" in name or name.endswith(".SHA1"):
        return "sha1"
    if "SHA256SUM" in name or name.endswith(".SHA256"):
        return "sha256"
    if "SHA512SUM" in name or name.endswith(".SHA512"):
        return "sha512"
    return None


def parse_checksum_file_line(
    line: str,
    line_num: int,
    format_hint: ChecksumFileFormat = "auto",
    default_algo_hint: Optional[SupportedChecksumAlgorithm] = None,
) -> Optional[ParsedChecksumEntry]:
    """
    Parses a single line from a checksum file.
    Tries to detect format (GNU or BSD) if format_hint is 'auto'.
    """
    stripped_line = line.strip()
    if not stripped_line or stripped_line.startswith("#"):
        return None

    entry: Optional[ParsedChecksumEntry] = None

    if format_hint == "auto" or format_hint == "bsd":
        bsd_match = BSD_LINE_RE.match(stripped_line)
        if bsd_match:
            data = bsd_match.groupdict()
            algo_name_upper = data["algo"].upper()
            parsed_algo = SUPPORTED_ALGORITHMS_MAP.get(algo_name_upper)
            if parsed_algo:
                entry = ParsedChecksumEntry(
                    filename=data["filename"],
                    expected_hash=data["hash"].lower(),
                    algorithm=parsed_algo,
                    original_line=stripped_line,
                    line_number=line_num,
                )
                return entry

    if format_hint == "auto" or format_hint == "gnu":
        gnu_match = GNU_LINE_RE.match(stripped_line)
        if gnu_match:
            data = gnu_match.groupdict()
            # For GNU, algorithm is often implied by file type or must be provided.
            entry = ParsedChecksumEntry(
                # GNU filenames might have leading/trailing spaces from spec
                filename=data["filename"].strip(),
                expected_hash=data["hash"].lower(),
                algorithm=default_algo_hint,  # Use hint if GNU, BSD would have found it
                original_line=stripped_line,
                line_number=line_num,
            )
            return entry  # GNU format successfully parsed

    return None


def parse_checksum_file(
    checksum_file_path: Path,
    format_hint: ChecksumFileFormat = "auto",
    default_algo_hint: Optional[SupportedChecksumAlgorithm] = None,
    logger: Optional[Logger] = None,
) -> List[ParsedChecksumEntry]:
    """
    Parses a checksum file (e.g., MD5SUMS, SHA256SUMS) and returns a list of entries.
    Handles common GNU and BSD style formats.
    """
    if not checksum_file_path.is_file():
        if logger:
            logger.error(f"Checksum file not found: {checksum_file_path}", emoji="❌")
        raise FileNotFoundError(f"Checksum file not found: {checksum_file_path}")

    entries: List[ParsedChecksumEntry] = []
    effective_default_algo = default_algo_hint
    if default_algo_hint == "auto" or default_algo_hint is None:
        effective_default_algo = get_algo_from_filename(checksum_file_path)
        if logger and effective_default_algo:
            logger.debug(
                f"Inferred algorithm '{effective_default_algo}' from checksum filename.",
                emoji="🤔",
            )

    try:
        with checksum_file_path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                parsed_entry = parse_checksum_file_line(
                    line,
                    i,
                    format_hint=format_hint,
                    default_algo_hint=effective_default_algo,
                )
                if parsed_entry:
                    # If entry itself didn't get an algo (e.g. GNU format and no default_algo_hint),
                    if parsed_entry.algorithm is None and effective_default_algo:
                        parsed_entry.algorithm = effective_default_algo

                    # Basic validation of hash length for known algorithms
                    if (
                        parsed_entry.algorithm == "md5"
                        and len(parsed_entry.expected_hash) != 32
                    ):
                        if logger:
                            logger.warn(
                                f"Line {i}: MD5 hash length incorrect: {parsed_entry.expected_hash}",
                                emoji="⚠️",
                            )
                        continue
                    if (
                        parsed_entry.algorithm == "sha1"
                        and len(parsed_entry.expected_hash) != 40
                    ):
                        if logger:
                            logger.warn(
                                f"Line {i}: SHA1 hash length incorrect: {parsed_entry.expected_hash}",
                                emoji="⚠️",
                            )
                        continue
                    if (
                        parsed_entry.algorithm == "sha256"
                        and len(parsed_entry.expected_hash) != 64
                    ):
                        if logger:
                            logger.warn(
                                f"Line {i}: SHA256 hash length incorrect: {parsed_entry.expected_hash}",
                                emoji="⚠️",
                            )
                        continue
                    if (
                        parsed_entry.algorithm == "sha512"
                        and len(parsed_entry.expected_hash) != 128
                    ):
                        if logger:
                            logger.warn(
                                f"Line {i}: SHA512 hash length incorrect: {parsed_entry.expected_hash}",
                                emoji="⚠️",
                            )
                        continue

                    entries.append(parsed_entry)
                elif line.strip() and not line.strip().startswith("#"):
                    if logger:
                        logger.warn(
                            f"Checksum file line {i} could not be parsed: {line.strip()}",
                            emoji="❓",
                        )

    except Exception as e:
        if logger:
            logger.error(
                f"Error reading or parsing checksum file {checksum_file_path}: {e}",
                emoji="💥",
            )
        raise IOError(
            f"Error processing checksum file {checksum_file_path}: {e}"
        ) from e

    if not entries and logger:
        logger.warn(
            f"No valid checksum entries found in {checksum_file_path}.", emoji="🤷"
        )

    return entries
