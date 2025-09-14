import click
import shutil
from pathlib import Path
from typing import List, Optional

from sigmate.config import SIGNATURES_FOLDER
from sigmate.cli.sign import DEFAULT_CHECKSUM_FILENAMES
from sigmate.utils.logger import Logger

# A set of critical paths that should never be cleaned.
PROTECTED_PATHS = {
    Path.home(),
    Path.home().parent,
    Path("/"),
    Path("/etc"),
    Path("/var"),
    Path("/usr"),
    Path("/tmp"),
}


@click.command("clean")
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, resolve_path=True, writable=True),
    required=False,
    default=None,
)
@click.pass_context
def clean_cmd(ctx: click.Context, path: Optional[str]):
    """
    Removes generated signature artifacts, always prompting for confirmation.

    If a PATH is provided, this command inspects that directory for artifacts.

    If no PATH is provided, it defaults to cleaning the './signatures'
    directory and any default checksum files from the current directory.
    """
    logger: Logger = ctx.obj["logger"]
    paths_to_delete: List[Path] = []

    scan_dir: Optional[Path] = Path(path) if path else Path.cwd() / SIGNATURES_FOLDER

    if not scan_dir.is_dir():
        logger.info(
            "Nothing to clean. No artifact directory specified or found.", emoji="✨"
        )
        return

    logger.info(f"Scanning for Sigmate artifacts in: {scan_dir}", emoji="🔍")

    if scan_dir.resolve() in PROTECTED_PATHS:
        raise click.ClickException(
            f"Error: Refusing to clean protected system directory: {scan_dir}"
        )

    meta_file = scan_dir / "sigmate.meta.json"
    sbom_file = scan_dir / "sigmate.sbom.json"

    if meta_file.is_file() or sbom_file.is_file():
        paths_to_delete.append(scan_dir)
    else:
        logger.warn(
            f"Directory '{scan_dir}' does not contain 'sigmate.meta.json' or 'sigmate.sbom.json'.",
            emoji="⚠️",
        )
        logger.warn(
            "This could be an output directory from a '--raw' only signing operation, or an unrelated folder.",
            emoji="ℹ️",
        )
        logger.warn(
            "To prevent accidental data loss, sigmate will not remove this directory automatically.",
            emoji="🛡️",
        )
        logger.warn("Please inspect and delete it manually if you are sure.", emoji="")

    if not path:
        for filename in DEFAULT_CHECKSUM_FILENAMES.values():
            checksum_file = Path.cwd() / filename
            if checksum_file.is_file():
                paths_to_delete.append(checksum_file)

    if not paths_to_delete:
        logger.info("No artifacts confirmed for cleanup.", emoji="✨")
        return

    logger.warn("The following will be PERMANENTLY DELETED:", emoji="🗑️")
    for p in paths_to_delete:
        item_type = "directory" if p.is_dir() else "file"
        logger.warn(f"  - {p} ({item_type})", emoji="")

    # The confirmation prompt is now mandatory.
    click.confirm("\nAre you sure you want to proceed?", abort=True, err=True)
    click.echo("")

    try:
        for p in paths_to_delete:
            if p.is_dir():
                shutil.rmtree(p)
                logger.debug(f"Removed directory: {p}", emoji="♻️")
            elif p.is_file():
                p.unlink()
                logger.debug(f"Removed file: {p}", emoji="♻️")
        logger.success(
            f"Cleaned up {len(paths_to_delete)} item(s) successfully.", emoji="✅"
        )
    except (IOError, OSError) as e:
        raise click.ClickException(f"Error during cleanup operation: {e}")
