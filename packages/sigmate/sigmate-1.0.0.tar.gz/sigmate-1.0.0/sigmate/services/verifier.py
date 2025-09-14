import json
import base64
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, cast

from sigmate.utils.hashing import file_hash
from sigmate.secops.signing import verify_signature
from sigmate.secops.keys import extract_public_key_fingerprint
from sigmate.secops.trust import TrustedKeyStore
from sigmate.utils.logger import Logger
from sigmate.utils.checksum_parser import (
    parse_checksum_file,
    ParsedChecksumEntry,
    ChecksumFileFormat,
    SupportedChecksumAlgorithm,
)


def _load_central_metadata(
    meta_file_path: Path, logger: Optional[Logger]
) -> Dict[str, Dict[str, Any]]:
    central_meta_store: Dict[str, Dict[str, Any]] = {}
    if not meta_file_path.is_file():
        return central_meta_store

    try:
        loaded_entries = json.loads(meta_file_path.read_text(encoding="utf-8"))
        if not isinstance(loaded_entries, list):
            if logger:
                logger.warn(f"Metadata file {meta_file_path} is not a JSON list. Skipping.", emoji="⚠️")
            return {}

        for entry in loaded_entries:
            relpath = entry.get("relpath")
            if relpath:
                central_meta_store[relpath] = entry
            elif logger:
                logger.warn(f"Skipping metadata entry with no 'relpath': {entry.get('file', 'N/A')}", emoji="❓")
    except (json.JSONDecodeError, IOError) as e:
        if logger:
            logger.error(f"Failed to parse central metadata file {meta_file_path}: {e}", emoji="❌")
    return central_meta_store


def resolve_signature_path(
    target_file: Path,
    sig_dir: Path,
    base_dir: Path,
    suffix: str,
) -> Optional[Path]:
    try:
        relative_path = target_file.resolve().relative_to(base_dir.resolve())
    except ValueError:
        relative_path = Path(target_file.name)

    artifact_path = (sig_dir.resolve() / relative_path).with_suffix(target_file.suffix + suffix)
    if artifact_path.is_file():
        return artifact_path

    artifact_path_fallback = sig_dir.resolve() / (target_file.name + suffix)
    if artifact_path_fallback.is_file():
        return artifact_path_fallback

    return None


def verify_files(
    files: List[Path],
    key_data: bytes,
    sig_type: str,
    sig_dir: Path,
    base_dir: Path,
    explicit_sigfile: Optional[Path] = None,
    require_trusted_key: bool = False,
    trusted_key_store: Optional[TrustedKeyStore] = None,
    logger: Optional[Logger] = None,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    public_key_fingerprint: Optional[str] = None
    try:
        public_key_fingerprint = extract_public_key_fingerprint(key_data)
    except ValueError as e:
        if logger:
            logger.error(f"Invalid public key provided: {e}", emoji="❌")
        return [{"file": str(f.resolve()), "error": f"Invalid public key: {e}", "overall_verified": False} for f in files]

    central_meta_file_path = sig_dir.resolve() / "sigmate.meta.json"
    central_meta_store = _load_central_metadata(central_meta_file_path, logger)

    for f_path in files:
        f_path_abs_str = str(f_path.resolve())
        result: Dict[str, Any] = {
            "file": f_path_abs_str,
            "signature_file": None,
            "metadata_source": None,
            "valid_signature": False,
            "expired": None,
            "trusted_signer": None,
            "error": None,
            "expected_hash": None,
            "actual_hash": None,
            "overall_verified": False,
        }

        try:
            file_data = f_path.read_bytes()
            result["actual_hash"] = file_hash(file_data, algo="sha256")

            if require_trusted_key and trusted_key_store and public_key_fingerprint:
                is_trusted = trusted_key_store.is_fingerprint_actively_trusted(public_key_fingerprint)
                result["trusted_signer"] = is_trusted
                if not is_trusted:
                    result["error"] = "Signer's public key is not actively trusted in the store."

            meta_from_file: Optional[Dict[str, Any]] = None
            signature_bytes: Optional[bytes] = None

            if sig_type == "meta":
                if not central_meta_store:
                    result["error"] = result["error"] or f"Metadata signature type specified but no metadata found at {central_meta_file_path}"
                else:
                    for relpath, entry in central_meta_store.items():
                        if f_path_abs_str.endswith(f"/{relpath}"):
                            meta_from_file = entry
                            result["metadata_source"] = str(central_meta_file_path)
                            break
            elif sig_type in ("auto", "raw"):
                raw_sig_path = resolve_signature_path(f_path, sig_dir, base_dir, ".sig")
                if raw_sig_path:
                    signature_bytes = raw_sig_path.read_bytes()
                    result["signature_file"] = str(raw_sig_path)
                elif sig_type == "auto" and central_meta_store:
                    for relpath, entry in central_meta_store.items():
                        if f_path_abs_str.endswith(f"/{relpath}"):
                            meta_from_file = entry
                            result["metadata_source"] = str(central_meta_file_path)
                            break

            if not meta_from_file and not signature_bytes:
                result["error"] = result["error"] or "No signature data found to verify."

            if meta_from_file:
                result["expected_hash"] = meta_from_file.get("file_hash")
                if result["actual_hash"] != result["expected_hash"]:
                    result["error"] = result["error"] or "File content hash does not match hash in metadata."

                expires_at_str = meta_from_file.get("expires_at")
                if expires_at_str:
                    try:
                        exp_dt = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                        result["expired"] = datetime.now(timezone.utc) > exp_dt
                        if result["expired"]:
                            result["error"] = result["error"] or "Signature has expired."
                    except ValueError:
                        result["error"] = result["error"] or "Invalid expiration timestamp in metadata."
                else:
                    # If no expiration date exists, it cannot be expired.
                    result["expired"] = False

                sig_b64 = meta_from_file.get("signature")
                if sig_b64:
                    try:
                        signature_bytes = base64.b64decode(sig_b64)
                    except Exception:
                        result["error"] = result["error"] or "Failed to decode base64 signature from metadata."

            if not result["error"] and signature_bytes:
                is_crypto_valid = verify_signature(file_data, signature_bytes, key_data)
                result["valid_signature"] = is_crypto_valid
                if not is_crypto_valid:
                    result["error"] = result["error"] or "Cryptographic signature verification failed."

            passes_hash = result["expected_hash"] is None or (result["actual_hash"] == result["expected_hash"])
            result["overall_verified"] = not result["error"] and passes_hash and result["valid_signature"]

        except Exception as e:
            result["error"] = f"An unexpected error occurred: {e}"

        final_result = {k: v for k, v in result.items() if v is not None}
        results.append(final_result)
        
    return results


def verify_files_from_checksum_file(
    files_to_verify: List[Path],
    checksum_file_path: Path,
    desired_algo_hint: str,
    format_hint: str,
    content_base_dir: Path,
    logger: Optional[Logger] = None,
) -> List[Dict[str, Any]]:
    results_checksum: List[Dict[str, Any]] = []
    try:
        parsed_checksum_entries = parse_checksum_file(
            checksum_file_path,
            format_hint=cast(ChecksumFileFormat, format_hint),
            default_algo_hint=cast(Optional[SupportedChecksumAlgorithm], desired_algo_hint if desired_algo_hint != "auto" else None),
            logger=logger,
        )
    except (FileNotFoundError, IOError, ValueError) as e:
        if logger:
            logger.error(f"Failed to process checksum file {checksum_file_path}: {e}", emoji="❌")
        return [{"file": str(f.resolve()), "status": "error", "error_message": f"Checksum file error: {e}"} for f in files_to_verify]

    checksum_map: Dict[str, ParsedChecksumEntry] = {entry.filename.lstrip("./"): entry for entry in parsed_checksum_entries}

    files_in_checksum_list = [content_base_dir / entry.filename.lstrip("./") for entry in parsed_checksum_entries if (content_base_dir / entry.filename.lstrip("./")).exists()]
    files_to_check = files_to_verify or files_in_checksum_list

    for local_file in files_to_check:
        local_file_abs = local_file.resolve()
        current_result: Dict[str, Any] = {"file": str(local_file_abs), "status": "pending"}
        try:
            relative_local_path_str = local_file_abs.relative_to(content_base_dir).as_posix()
            checksum_entry = checksum_map.get(relative_local_path_str) or checksum_map.get(relative_local_path_str.lstrip("./"))

            if not checksum_entry:
                current_result["status"] = "not_found_in_checksum_file"
            else:
                current_result["expected_hash"] = checksum_entry.expected_hash
                algo_to_use = cast(Optional[SupportedChecksumAlgorithm], (desired_algo_hint if desired_algo_hint != "auto" else checksum_entry.algorithm))

                if not algo_to_use:
                    current_result["status"] = "error"
                    current_result["error_message"] = f"Algorithm for '{relative_local_path_str}' is ambiguous."
                else:
                    current_result["algorithm_used"] = algo_to_use
                    actual_hash_val = file_hash(local_file_abs.read_bytes(), algo=algo_to_use)
                    current_result["actual_hash"] = actual_hash_val
                    current_result["status"] = "match" if actual_hash_val.lower() == checksum_entry.expected_hash.lower() else "mismatch"
        except Exception as e:
            current_result["status"] = "error"
            current_result["error_message"] = f"Verification error: {e}"
        
        final_result = {k: v for k, v in current_result.items() if v is not None}
        results_checksum.append(final_result)
        
    return results_checksum
