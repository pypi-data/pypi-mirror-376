import os
import socket
import click
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from sigmate.config import SIGNATURES_FOLDER
from sigmate.managers.config import ConfigManager
from sigmate.utils.git import get_git_info_object, get_git_author
from sigmate.utils.files import collect_files, should_skip_file
from sigmate.utils.print import print_json
from sigmate.services.signer import sign_files
from sigmate.utils.logger import Logger
from sigmate.secops.keys import load_private_key_ed25519

DEFAULT_CHECKSUM_FILENAMES: Dict[str, str] = {
    "md5": "MD5SUMS",
    "sha1": "SHA1SUMS",
    "sha256": "SHA256SUMS",
    "sha512": "SHA512SUMS",
}


def _get_display_path(path_str: Optional[str]) -> str:
    """Safely converts a path string to a relative string for display."""
    if not path_str:
        return ""
    path_obj = Path(path_str)
    if path_obj.is_absolute():
        try:
            return str(path_obj.relative_to(Path.cwd()))
        except ValueError:
            return path_str
    return path_str


@click.command("sign")
@click.argument(
    "target_path_or_file",
    type=click.Path(exists=True, resolve_path=True),
    required=False,
    default=None,
    metavar="TARGET",
)
@click.option(
    "--key",
    "private_key_pem_path",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    required=False,
    help="Path to private key (PEM). Overrides configured default.",
)
@click.option(
    "--key-password-env",
    "key_password_env_var",
    type=str,
    default=None,
    help="Environment variable for the private key password (for CI/CD).",
)
@click.option(
    "--signatures-output",
    "signatures_output_directory_path",
    type=click.Path(file_okay=False, writable=True, resolve_path=True),
    help="Base directory for all generated files.",
)
@click.option(
    "--walk",
    "walk_directory_path",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help="Directory to recursively process.",
)
@click.option(
    "--list",
    "--file-list",
    "file_list_path",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help="Text file listing files/directories to process.",
)
@click.option("--raw", is_flag=True, help="Output raw Ed25519 .sig file.")
@click.option("--meta", is_flag=True, help="Output sigmate.meta.json.")
@click.option("--both", is_flag=True, help="Output both .sig and sigmate.meta.json.")
@click.option(
    "--sbom", is_flag=True, help="Generate CycloneDX SBOM (sigmate.sbom.json)."
)
@click.option(
    "--json", "json_output", is_flag=True, help="Print a JSON summary of operations."
)
@click.option(
    "--identity",
    default=None,
    help="Override signer identity. Overrides configured default.",
)
@click.option("--host", default=None, help="Override host name for metadata.")
@click.option(
    "--expires-in",
    type=int,
    default=None,
    help="Expiration for signatures in hours (e.g., 72).",
)
@click.option(
    "--no-abspath",
    is_flag=True,
    help="Exclude absolute file paths in metadata and SBOMs.",
)
@click.option(
    "--gen-md5sums",
    "md5sums_out_name",
    type=str,
    default=None,
    is_flag=False,
    flag_value=DEFAULT_CHECKSUM_FILENAMES["md5"],
    help="Generate MD5SUMS file.",
)
@click.option(
    "--gen-sha1sums",
    "sha1sums_out_name",
    type=str,
    default=None,
    is_flag=False,
    flag_value=DEFAULT_CHECKSUM_FILENAMES["sha1"],
    help="Generate SHA1SUMS file.",
)
@click.option(
    "--gen-sha256sums",
    "sha256sums_out_name",
    type=str,
    default=None,
    is_flag=False,
    flag_value=DEFAULT_CHECKSUM_FILENAMES["sha256"],
    help="Generate SHA256SUMS file.",
)
@click.option(
    "--gen-sha512sums",
    "sha512sums_out_name",
    type=str,
    default=None,
    is_flag=False,
    flag_value=DEFAULT_CHECKSUM_FILENAMES["sha512"],
    help="Generate SHA512SUMS file.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing signature and checksum artifacts.",
)
@click.pass_context
def sign_cmd(
    ctx: click.Context,
    target_path_or_file: Optional[str],
    private_key_pem_path: Optional[str],
    key_password_env_var: Optional[str],
    signatures_output_directory_path: Optional[str],
    walk_directory_path: Optional[str],
    file_list_path: Optional[str],
    raw: bool,
    meta: bool,
    both: bool,
    sbom: bool,
    json_output: bool,
    identity: Optional[str],
    host: Optional[str],
    expires_in: Optional[int],
    no_abspath: bool,
    md5sums_out_name: Optional[str],
    sha1sums_out_name: Optional[str],
    sha256sums_out_name: Optional[str],
    sha512sums_out_name: Optional[str],
    force: bool,
):
    """Generates Ed25519 signatures and/or traditional checksum files."""
    logger: Logger = ctx.obj["logger"]
    config = ConfigManager()

    effective_key_path = private_key_pem_path or config.get("private_key_path")
    effective_identity = identity or config.get("signer_identity") or get_git_author()

    key_data: Optional[bytes] = None
    password_bytes: Optional[bytes] = None
    if effective_key_path:
        try:
            key_data = Path(effective_key_path).read_bytes()
            load_private_key_ed25519(key_data, password=None)
        except ValueError as e:
            if "encrypted" in str(e).lower() or "password" in str(e).lower():
                if key_password_env_var:
                    password_str = os.getenv(key_password_env_var)
                    if not password_str:
                        raise click.ClickException(
                            f"Key is encrypted, but environment variable '{key_password_env_var}' is not set."
                        )
                else:
                    password_str = click.prompt(
                        "Enter password for private key", hide_input=True, err=True
                    )
                password_bytes = password_str.encode("utf-8")
                try:
                    load_private_key_ed25519(key_data, password=password_bytes)
                except ValueError as e2:
                    raise click.ClickException(f"Incorrect password or corrupt key: {e2}")
            else:
                raise click.ClickException(f"Invalid private key: {e}")
        except Exception as e:
            raise click.ClickException(
                f"Failed to load private key {effective_key_path}: {e}"
            )

    is_crypto_signing_active = bool(key_data)
    if (raw or meta or both or sbom) and not is_crypto_signing_active:
        raise click.UsageError(
            "A private key must be provided via the --key flag or set via 'sigmate configure'."
        )

    checksum_generation_tasks: List[Dict[str, str]] = []
    if md5sums_out_name:
        checksum_generation_tasks.append(
            {"algo": "md5", "output_filename": md5sums_out_name}
        )
    if sha1sums_out_name:
        checksum_generation_tasks.append(
            {"algo": "sha1", "output_filename": sha1sums_out_name}
        )
        if not json_output:
            logger.warn(
                "SHA1 is cryptographically weak and should not be used for security purposes.",
                emoji="⚠️",
            )
    if sha256sums_out_name:
        checksum_generation_tasks.append(
            {"algo": "sha256", "output_filename": sha256sums_out_name}
        )
    if sha512sums_out_name:
        checksum_generation_tasks.append(
            {"algo": "sha512", "output_filename": sha512sums_out_name}
        )

    if not is_crypto_signing_active and not checksum_generation_tasks:
        raise click.UsageError(
            "No operation specified. Provide --key or --gen-<algo>sums options."
        )

    if signatures_output_directory_path:
        effective_output_dir = Path(signatures_output_directory_path)
    elif is_crypto_signing_active:
        effective_output_dir = Path.cwd() / SIGNATURES_FOLDER
    else:
        effective_output_dir = Path.cwd()

    try:
        effective_output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise click.ClickException(
            f"Failed to create output directory {effective_output_dir}: {e}"
        )

    files_to_process: List[Path] = []
    base_dir: Path
    if walk_directory_path:
        base_dir = Path(walk_directory_path)
        files_to_process = collect_files(base_dir, logger=logger)
    elif file_list_path:
        base_dir = Path.cwd()
        list_p = Path(file_list_path)
        try:
            with list_p.open("r", encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if not stripped_line or stripped_line.startswith("#"):
                        continue
                    path_in_list = base_dir / stripped_line
                    if not path_in_list.exists():
                        if not json_output:
                            logger.warn(
                                f"Path from list not found, skipping: {path_in_list}",
                                emoji="❓",
                            )
                        continue
                    if path_in_list.is_file():
                        if not should_skip_file(path_in_list):
                            files_to_process.append(path_in_list)
                    elif path_in_list.is_dir():
                        files_to_process.extend(
                            collect_files(path_in_list, logger=logger)
                        )
        except IOError as e:
            raise click.ClickException(
                f"Could not read file list {file_list_path}: {e}"
            )
    elif target_path_or_file:
        target_p = Path(target_path_or_file)
        if target_p.is_file():
            files_to_process, base_dir = [target_p], target_p.parent
        else:
            base_dir = target_p
            files_to_process = collect_files(base_dir, logger=logger)
    else:
        raise click.UsageError(
            "Must specify a TARGET path/file, or use --walk or --list."
        )

    if not files_to_process:
        if not json_output:
            logger.warn("No files found to process with the given inputs.", emoji="🤷")
        else:
            print_json({"status": "no_files", "message": "No files found to process."})
        return

    effective_raw, effective_meta = (True, True) if both else (raw, meta)
    git_info_for_metadata = get_git_info_object(base_dir)
    current_host = host or os.getenv("SIGMATE_HOST") or socket.gethostname()

    expires_at_iso: Optional[str] = None
    if expires_in is not None:
        if expires_in <= 0:
            raise click.BadOptionUsage("expires-in", "Must be a positive integer.")
        expires_at_iso = (
            (datetime.now(timezone.utc) + timedelta(hours=expires_in))
            .isoformat()
            .replace("+00:00", "Z")
        )

    if not json_output:
        logger.info(
            f"Preparing to process {len(files_to_process)} file(s). Base directory for relative paths: {base_dir}",
            emoji="⚙️",
        )

    logger_to_pass = logger if not json_output else None
    operation_results = sign_files(
        files=files_to_process,
        key_data=key_data,
        output_dir=effective_output_dir,
        base_dir=base_dir,
        identity=effective_identity,
        host=current_host,
        version=git_info_for_metadata,
        raw=effective_raw if is_crypto_signing_active else False,
        meta=effective_meta if is_crypto_signing_active else False,
        sbom=sbom if is_crypto_signing_active else False,
        no_abspath=no_abspath,
        expires_at=expires_at_iso,
        checksum_tasks=checksum_generation_tasks,
        logger=logger_to_pass,
        force=force,
        password=password_bytes,
    )

    if not json_output:
        crypto_summary = operation_results.get("crypto_signing_summary", {})
        if crypto_summary.get("active"):
            signed_count = sum(
                1
                for r in crypto_summary.get("details", [])
                if r.get("status") == "signed"
            )
            if signed_count > 0:
                logger.success(
                    f"Ed25519 signing: {signed_count} file(s) processed successfully.",
                    emoji="✅",
                )

            meta_display_path = _get_display_path(crypto_summary.get("meta_file_path"))
            if meta_display_path:
                logger.info(f"  ↳ Metadata file: {meta_display_path}", emoji="🧾")

            sbom_display_path = _get_display_path(crypto_summary.get("sbom_file_path"))
            if sbom_display_path:
                logger.info(f"  ↳ SBOM file: {sbom_display_path}", emoji="📦")

        checksum_summary = operation_results.get("checksum_generation_summary", {})
        if checksum_summary.get("active"):
            for task_res in checksum_summary.get("tasks_summary", []):
                display_path = _get_display_path(task_res.get("path"))
                if task_res.get("status") == "generated":
                    logger.success(
                        f"Generated checksum file: {display_path} ({task_res.get('count', 0)} entries)",
                        emoji="🧮",
                    )
                elif task_res.get("status") == "error":
                    logger.error(
                        f"Failed to generate checksum file {display_path}: {task_res.get('error')}",
                        emoji="❌",
                    )
                elif task_res.get("status") == "skipped_exists":
                    logger.warn(
                        f"Checksum file already exists, skipping: {display_path}",
                        emoji="🛡️",
                    )

        if operation_results.get("overall_status") != "success":
            logger.error(
                "Some operations did not complete successfully. Please review output.",
                emoji="⚠️",
            )
            ctx.exit(1)
        else:
            if is_crypto_signing_active or checksum_generation_tasks:
                logger.info(
                    "All requested operations finished successfully.", emoji="🎉"
                )
    else:
        print_json(operation_results)
        if operation_results.get("overall_status") != "success":
            ctx.exit(1)
