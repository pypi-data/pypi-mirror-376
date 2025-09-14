import click
from pathlib import Path
from typing import Optional, List, Dict, Any

from sigmate.config import SIGNATURES_FOLDER
from sigmate.managers.config import ConfigManager
from sigmate.utils.print import print_json
from sigmate.utils.files import collect_files, should_skip_file
from sigmate.services.verifier import verify_files, verify_files_from_checksum_file
from sigmate.secops.trust import TrustedKeyStore
from sigmate.cli.trust import TRUSTED_KEYS_PATH, _sanitize_filename
from sigmate.utils.logger import Logger


def _print_crypto_result(result: Dict[str, Any], logger: Logger):
    file_path_str = result.get("file", "Unknown")
    file_path = Path(file_path_str).name
    
    if result.get("overall_verified"):
        logger.success(f"VERIFIED: {file_path}", emoji="✅")
    else:
        logger.error(f"FAILED: {file_path}", emoji="❌")

    source = result.get("metadata_source") or result.get("signature_file")
    if source:
        logger.info(f"  ├─ Source: {Path(source).name}", emoji="")

    if result.get("expected_hash"):
        is_match = result["actual_hash"] == result["expected_hash"]
        status_text = "Matches" if is_match else "MISMATCH"
        log_func = logger.success if is_match else logger.error
        log_func(f"  ├─ Content Hash:  {status_text}", emoji="")
        if not is_match:
            logger.error(f"  │  ├─ Expected: {result['expected_hash']}", emoji="")
            logger.error(f"  │  └─ Actual:   {result['actual_hash']}", emoji="")

    if result.get("valid_signature") is not None:
        is_valid = result["valid_signature"]
        status_text = "Valid" if is_valid else "INVALID"
        log_func = logger.success if is_valid else logger.error
        log_func(f"  ├─ Signature:       {status_text}", emoji="")

    if result.get("expired") is not None:
        is_expired = result["expired"]
        status_text = "EXPIRED" if is_expired else "OK"
        log_func = logger.warn if is_expired else logger.success
        log_func(f"  ├─ Expiration:    {status_text}", emoji="")
        
    # Determine the final character for the tree structure
    is_last_item = not result.get("error")
    tree_char = "└─" if is_last_item else "├─"

    if result.get("trusted_signer") is not None:
        is_trusted = result["trusted_signer"]
        status_text = "Trusted" if is_trusted else "NOT TRUSTED"
        log_func = logger.success if is_trusted else logger.warn
        log_func(f"  {tree_char} Signer Trust:  {status_text}", emoji="")
        if not is_trusted:
            is_last_item = not result.get("error") # re-evaluate for the next line
            tree_char = "└─" if is_last_item else "├─"
            
    if result.get("error"):
        logger.error(f"  └─ Error: {result['error']}", emoji="")


def _print_checksum_result(result: Dict[str, Any], logger: Logger):
    file_path = Path(result.get("file", "Unknown")).name
    status = result.get("status", "error")
    algo = result.get("algorithm_used", "unknown").upper()

    if status == "match":
        logger.success(f"MATCH: {file_path} ({algo})", emoji="✅")
    elif status == "mismatch":
        logger.error(f"MISMATCH: {file_path} ({algo})", emoji="❌")
        logger.error(f"  ├─ Expected: {result.get('expected_hash')}", emoji="")
        logger.error(f"  └─ Actual:   {result.get('actual_hash')}", emoji="")
    elif status == "not_found_in_checksum_file":
        logger.warn(f"NOT FOUND: {file_path}", emoji="❓")
    else:
        logger.error(f"ERROR: {file_path}", emoji="💥")
        logger.error(f"  └─ {result.get('error_message')}", emoji="")


@click.command("verify")
@click.argument(
    "target_path_or_file",
    type=click.Path(exists=True, resolve_path=True),
    required=False,
    default=None,
    metavar="TARGET",
)
@click.option(
    "--key",
    "public_key_pem_path",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    required=False,
    help="Path to a public key (PEM) for verification.",
)
@click.option(
    "--signer",
    "signer_name",
    help="Verify using a trusted signer's name from the keyring.",
)
@click.option(
    "--signature",
    "explicit_signature_file_path",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help="Explicit Ed25519 signature file (.sig or .sigmeta.json).",
)
@click.option(
    "--sig-type",
    "ed25519_sig_type",
    type=click.Choice(["auto", "raw", "meta"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="Format of Ed25519 signature to expect or use.",
)
@click.option(
    "--signatures-input",
    "ed25519_signatures_input_dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help="Directory containing Ed25519 signature files (default: CWD/signatures or alongside files).",
)
@click.option(
    "--require-trusted",
    is_flag=True,
    help="For Ed25519: enforce that the signer's public key is in the trusted key store and 'verified'.",
)
@click.option(
    "--checksum-file",
    "checksum_file_path_str",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    default=None,
    help="Path to the checksum file (e.g., MD5SUMS, SHA256SUMS) for verification.",
)
@click.option(
    "--checksum-algo",
    "checksum_algorithm",
    type=click.Choice(
        ["auto", "md5", "sha1", "sha256", "sha512"], case_sensitive=False
    ),
    default="auto",
    show_default=True,
    help="Algorithm for checksum verification. 'auto' attempts to infer.",
)
@click.option(
    "--checksum-format",
    "checksum_file_format",
    type=click.Choice(["auto", "gnu", "bsd"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="Format of the checksum file. 'auto' attempts to parse common formats.",
)
@click.option(
    "--walk",
    "walk_directory_path",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help="Directory to recursively verify. Overrides TARGET if TARGET is a directory.",
)
@click.option(
    "--list",
    "--file-list",
    "file_list_path",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help="Text file listing files/directories to verify.",
)
@click.option(
    "--json", "json_output", is_flag=True, help="Output result as structured JSON."
)
@click.option("--no-abspath", is_flag=True, help="Use relative paths in JSON output.")
@click.pass_context
def verify_cmd(
    ctx: click.Context,
    target_path_or_file: Optional[str],
    public_key_pem_path: Optional[str],
    signer_name: Optional[str],
    explicit_signature_file_path: Optional[str],
    ed25519_sig_type: str,
    ed25519_signatures_input_dir: Optional[str],
    require_trusted: bool,
    checksum_file_path_str: Optional[str],
    checksum_algorithm: str,
    checksum_file_format: str,
    walk_directory_path: Optional[str],
    file_list_path: Optional[str],
    json_output: bool,
    no_abspath: bool,
):
    """Verifies files using Ed25519 signatures OR traditional checksum files."""
    logger: Logger = ctx.obj["logger"]
    is_checksum_mode = bool(checksum_file_path_str)

    effective_key_path = public_key_pem_path
    if signer_name:
        if public_key_pem_path:
            raise click.UsageError("Cannot use --key and --signer at the same time.")
        config = ConfigManager()
        keyring_path = config.get_keyring_path()
        key_alias = _sanitize_filename(signer_name)
        potential_key_path = keyring_path / f"{key_alias}.pub"
        if not potential_key_path.is_file():
            raise click.ClickException(
                f"Signer '{signer_name}' not found in keyring: {potential_key_path}"
            )
        effective_key_path = str(potential_key_path)

    is_crypto_mode = bool(effective_key_path)

    if is_crypto_mode and is_checksum_mode:
        raise click.UsageError(
            "Cannot use --key/--signer and --checksum-file simultaneously."
        )
    if not is_crypto_mode and not is_checksum_mode:
        raise click.UsageError("Must specify either --key/--signer or --checksum-file.")

    files_to_verify: List[Path] = []
    content_base_dir: Path
    if walk_directory_path:
        content_base_dir = Path(walk_directory_path)
        files_to_verify = collect_files(content_base_dir, logger=logger)
    elif file_list_path:
        content_base_dir = Path.cwd()
        list_p = Path(file_list_path)
        try:
            with list_p.open("r", encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if not stripped_line or stripped_line.startswith("#"):
                        continue
                    path_in_list = content_base_dir / stripped_line
                    if not path_in_list.exists():
                        if not json_output:
                            logger.warn(
                                f"Path from list not found, skipping: {path_in_list}",
                                emoji="❓",
                            )
                        continue
                    if path_in_list.is_file():
                        if not should_skip_file(path_in_list):
                            files_to_verify.append(path_in_list)
                    elif path_in_list.is_dir():
                        files_to_verify.extend(
                            collect_files(path_in_list, logger=logger)
                        )
        except IOError as e:
            raise click.ClickException(
                f"Could not read file list {file_list_path}: {e}"
            )
    elif target_path_or_file:
        target_p = Path(target_path_or_file)
        if target_p.is_file():
            files_to_verify, content_base_dir = [target_p], target_p.parent
        else:
            content_base_dir = target_p
            files_to_verify = collect_files(content_base_dir, logger=logger)
    else:
        if not is_checksum_mode:
            raise click.UsageError(
                "Must specify a TARGET, --walk, or --list for cryptographic verification."
            )
        content_base_dir = Path.cwd()

    if not files_to_verify and is_crypto_mode:
        if not json_output:
            logger.warn(
                "No files found to verify based on the provided input.", emoji="🤷"
            )
        else:
            print_json({"status": "no_files", "results": []})
        return

    results: List[Dict[str, Any]] = []
    all_verified = True
    project_root_for_paths = content_base_dir
    logger_to_pass = logger if not json_output else None

    if is_crypto_mode:
        key_data = Path(effective_key_path).read_bytes()
        sig_dir_for_crypto = (
            Path(ed25519_signatures_input_dir)
            if ed25519_signatures_input_dir
            else (Path.cwd() / SIGNATURES_FOLDER)
        )
        base_dir_for_service = (
            content_base_dir
            if ed25519_sig_type != "meta"
            else sig_dir_for_crypto.parent
        )
        if not json_output:
            logger.debug(
                f"Verifying files in {content_base_dir} using base directory {base_dir_for_service} for lookups.",
                emoji="🗺️",
            )
        trusted_key_store_instance = (
            TrustedKeyStore(TRUSTED_KEYS_PATH) if require_trusted else None
        )
        results = verify_files(
            files=files_to_verify,
            key_data=key_data,
            sig_type=ed25519_sig_type,
            sig_dir=sig_dir_for_crypto,
            base_dir=base_dir_for_service,
            explicit_sigfile=(
                Path(explicit_signature_file_path)
                if explicit_signature_file_path
                else None
            ),
            require_trusted_key=require_trusted,
            trusted_key_store=trusted_key_store_instance,
            logger=logger_to_pass,
        )
        all_verified = all(r.get("overall_verified", False) for r in results)

    elif is_checksum_mode:
        checksum_file_p = Path(checksum_file_path_str)
        project_root_for_paths = checksum_file_p.parent
        if not walk_directory_path and not target_path_or_file and not file_list_path:
            content_base_dir = project_root_for_paths
        results = verify_files_from_checksum_file(
            files_to_verify=files_to_verify,
            checksum_file_path=checksum_file_p,
            desired_algo_hint=checksum_algorithm,
            format_hint=checksum_file_format,
            content_base_dir=content_base_dir,
            logger=logger_to_pass,
        )
        all_verified = not any(
            r["status"] == "mismatch" or r["status"] == "error" for r in results
        )

    if json_output:
        if no_abspath:
            for item in results:
                for key in ["file", "metadata_source", "signature_file"]:
                    if item.get(key) and Path(item[key]).is_absolute():
                        try:
                            item[key] = str(
                                Path(item[key]).relative_to(project_root_for_paths)
                            )
                        except ValueError:
                            pass
        print_json(results)
    else:
        if results:
            logger.info("-" * 40, emoji="")
        for i, r_item in enumerate(results):
            if is_crypto_mode:
                _print_crypto_result(r_item, logger)
            else:
                _print_checksum_result(r_item, logger)
            if i < len(results) - 1:
                logger.info(" ", emoji="") # Creates a blank line
        if results:
            logger.info("-" * 40, emoji="")

    if not all_verified:
        ctx.exit(1)
