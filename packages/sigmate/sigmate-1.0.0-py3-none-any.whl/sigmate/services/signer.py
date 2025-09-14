import base64
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from sigmate.config import SIGMATE_VERSION
from sigmate.utils.files import should_skip_file, build_output_path
from sigmate.utils.hashing import file_hash
from sigmate.sbom.generate import generate_sbom_entry, build_cyclonedx_sbom
from sigmate.secops.keys import extract_public_key_fingerprint
from sigmate.secops.signing import sign_data
from sigmate.utils.logger import Logger


def sign_files(
    files: List[Path],
    key_data: Optional[bytes],
    output_dir: Path,
    base_dir: Path,
    identity: str,
    host: str,
    version: Optional[Dict[str, Any]],
    raw: bool,
    meta: bool,
    sbom: bool,
    no_abspath: bool,
    expires_at: Optional[str],
    checksum_tasks: List[Dict[str, str]],
    logger: Optional[Logger],
    force: bool,
    password: Optional[bytes],
) -> Dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    files_processed: List[Dict[str, Any]] = []
    files_skipped_count = 0
    meta_file_entries: List[Dict[str, Any]] = []
    sbom_file_components: List[Dict[str, Any]] = []

    collected_checksums: Dict[str, List[Tuple[str, str]]] = {
        task["algo"]: [] for task in checksum_tasks
    }

    is_crypto_signing_active = bool(key_data)
    key_fingerprint_for_signing: Optional[str] = None

    if is_crypto_signing_active and key_data:
        try:
            key_fingerprint_for_signing = extract_public_key_fingerprint(
                key_data, password=password
            )
        except ValueError as e:
            if logger:
                logger.error(f"Invalid private key: {e}", emoji="❌")
            # Return a flat error structure
            return {"overall_status": "failure", "error": f"Invalid private key: {e}"}


    for f_path in files:
        if should_skip_file(f_path):
            if logger:
                logger.debug(f"Skipping ignored file: {f_path}", emoji="🚫")
            files_skipped_count += 1
            continue

        try:
            if logger:
                logger.debug(f"Processing: {f_path}", emoji="✍️")

            file_data = f_path.read_bytes()

            if checksum_tasks:
                try:
                    relative_file_path_obj = f_path.resolve().relative_to(base_dir.resolve())
                except ValueError:
                    relative_file_path_obj = Path(f_path.name)
                
                relative_path_for_checksum = (f"./{relative_file_path_obj.as_posix()}" if relative_file_path_obj.parent == Path(".") else relative_file_path_obj.as_posix())
                for task in checksum_tasks:
                    algo = task["algo"]
                    checksum_value = file_hash(file_data, algo=algo)
                    collected_checksums[algo].append((relative_path_for_checksum, checksum_value))

            if is_crypto_signing_active and key_data:
                meta_entry = _create_meta_entry(f_path, base_dir, file_data, key_data, password, key_fingerprint_for_signing, raw, output_dir, no_abspath, now_iso, expires_at, identity, host, version)
                
                if meta:
                    meta_file_entries.append(meta_entry)
                if sbom:
                    sbom_file_components.append(generate_sbom_entry(f_path, meta_entry, f_path.relative_to(base_dir), not no_abspath))

            files_processed.append({"file": str(f_path), "status": "processed"})

        except Exception as e:
            if logger:
                logger.error(f"Failed to process file {f_path}: {e}", emoji="❌")
            files_processed.append({"file": str(f_path), "status": "error", "error": str(e)})


    meta_file_path_str = _write_meta_file(meta, is_crypto_signing_active, meta_file_entries, output_dir, force, logger)
    sbom_file_path_str = _write_sbom_file(sbom, is_crypto_signing_active, sbom_file_components, output_dir, force, logger)
    checksum_generation_details = _write_checksum_files(checksum_tasks, collected_checksums, output_dir, force, no_abspath, logger)

    final_summary_status = "success"
    if any(r.get("status") == "error" for r in files_processed):
        final_summary_status = "partial_failure"

    return {
        "overall_status": final_summary_status,
        "files_processed_count": len(files_processed),
        "files_skipped_count": files_skipped_count,
        "meta_file_path": meta_file_path_str,
        "sbom_file_path": sbom_file_path_str,
        "checksum_files_generated": [
            task["path"] for task in checksum_generation_details if task.get("status") == "generated"
        ],
    }


def _create_meta_entry(f_path, base_dir, file_data, key_data, password, key_fingerprint, raw, output_dir, no_abspath, now_iso, expires_at, identity, host, version):
    sig_bytes = sign_data(file_data, key_data, password=password)
    sig_b64 = base64.b64encode(sig_bytes).decode("utf-8")
    
    signature_file_path_for_meta = None
    if raw:
        sig_output_path = build_output_path(f_path, base_dir, ".sig", output_dir)
        sig_output_path.write_bytes(sig_bytes)
        if no_abspath:
            try:
                signature_file_path_for_meta = str(sig_output_path.relative_to(output_dir.parent))
            except ValueError:
                signature_file_path_for_meta = str(sig_output_path.relative_to(Path.cwd()))
        else:
            signature_file_path_for_meta = str(sig_output_path)

    meta_entry = {
        "file": f_path.name,
        "relpath": f_path.relative_to(base_dir).as_posix(),
        "abspath": str(f_path.resolve()) if not no_abspath else None,
        "created_at": now_iso,
        "expires_at": expires_at,
        "tool": {"name": "sigmate", "version": SIGMATE_VERSION, "language": "python"},
        "signer_identity": identity,
        "signer_host": host,
        "signature_algorithm": "Ed25519",
        "hash_algorithm": "sha256",
        "file_hash": file_hash(file_data, algo="sha256"),
        "signature": sig_b64,
        "signature_hash": file_hash(sig_bytes, algo="sha256"),
        "key_fingerprint": key_fingerprint,
        "signature_file": signature_file_path_for_meta,
        "version": version,
    }
    return {k: v for k, v in meta_entry.items() if v is not None}

def _write_meta_file(meta, is_active, entries, output_dir, force, logger):
    if not (is_active and meta and entries):
        return None
    meta_path = output_dir / "sigmate.meta.json"
    if meta_path.exists() and not force:
        if logger:
            logger.warn(f"Metadata file exists, skipping: {meta_path} (use --force)", emoji="🛡️")
        return str(meta_path)
    try:
        meta_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        return str(meta_path)
    except Exception as e:
        if logger:
            logger.error(f"Failed to write metadata file {meta_path}: {e}", emoji="❌")
        return None

def _write_sbom_file(sbom, is_active, components, output_dir, force, logger):
    if not (is_active and sbom and components):
        return None
    sbom_path = output_dir / "sigmate.sbom.json"
    if sbom_path.exists() and not force:
        if logger:
            logger.warn(f"SBOM file exists, skipping: {sbom_path} (use --force)", emoji="🛡️")
        return str(sbom_path)
    try:
        sbom_data = build_cyclonedx_sbom(components)
        sbom_path.write_text(json.dumps(sbom_data, indent=2), encoding="utf-8")
        return str(sbom_path)
    except Exception as e:
        if logger:
            logger.error(f"Failed to write SBOM file {sbom_path}: {e}", emoji="❌")
        return None

def _write_checksum_files(checksum_tasks, collected_checksums, output_dir, force, no_abspath, logger):
    details = []
    if not checksum_tasks:
        return details
    for task in checksum_tasks:
        algo, out_filename = task["algo"], task["output_filename"]
        checksum_file_path = output_dir / out_filename
        
        path_for_summary = ""
        if no_abspath:
            try:
                path_for_summary = str(checksum_file_path.relative_to(output_dir.parent))
            except ValueError:
                path_for_summary = str(checksum_file_path.relative_to(Path.cwd()))
        else:
            path_for_summary = str(checksum_file_path)

        task_detail = {"algo": algo, "path": path_for_summary, "status": "pending"}
        if checksum_file_path.exists() and not force:
            if logger:
                logger.warn(f"Checksum file exists, skipping: {checksum_file_path} (use --force)", emoji="🛡️")
            task_detail["status"] = "skipped_exists"
        else:
            try:
                lines = [f"{h}  {r}\n" for r, h in collected_checksums.get(algo, [])]
                checksum_file_path.write_text("".join(lines), encoding="utf-8")
                task_detail["status"], task_detail["count"] = "generated", len(lines)
            except Exception as e:
                task_detail["status"], task_detail["error"] = "error", str(e)
        details.append(task_detail)
    return details
