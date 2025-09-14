import click
from pathlib import Path
import json
import shutil
import re

from sigmate.secops.keys import extract_public_key_fingerprint_and_algo
from sigmate.secops.trust import TrustedKeyStore, VALID_VERIFICATION_STATUSES
from sigmate.config import TRUSTED_KEYS_FILENAME
from sigmate.managers.config import ConfigManager

TRUSTED_KEYS_PATH = Path.home() / TRUSTED_KEYS_FILENAME


def _sanitize_filename(name: str) -> str:
    """Removes characters that are unsafe for filenames."""
    name = re.sub(r'[<>()[\]{}|\\/?*&^%$#@!~`\'":;]', "", name)
    name = re.sub(r"[\s./]+", "_", name)
    return name


@click.group("trust")
def trust_cmd():
    """Manage trusted public keys and the keyring."""
    pass


@trust_cmd.command("add")
@click.argument(
    "keyfile", type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    "--name", required=True, help="A unique, memorable name (alias) for this key."
)
@click.option("--org", required=False, help="Signer organization (optional).")
@click.option(
    "--added-by", required=True, help="User or entity adding this key to the store."
)
def add_cmd(keyfile: str, name: str, org: str | None, added_by: str):
    """
    Add a public key to the trust store and copy it to the keyring.

    This makes the key available for verification using its --name.
    The key's algorithm will be auto-detected.
    """
    key_path = Path(keyfile)
    config = ConfigManager()
    keyring_path = config.get_keyring_path()

    key_alias = _sanitize_filename(name)
    if not key_alias:
        raise click.ClickException(
            "The provided --name is invalid or results in an empty alias."
        )

    keyring_dest_path = keyring_path / f"{key_alias}.pub"

    if keyring_dest_path.exists():
        raise click.ClickException(
            f"A key with the name '{name}' (alias: '{key_alias}') already exists in the keyring at:\n{keyring_dest_path}"
        )

    try:
        key_data = key_path.read_bytes()
        fpr, detected_algo = extract_public_key_fingerprint_and_algo(key_data)
    except ValueError as e:
        raise click.ClickException(f"Error processing key file {key_path}: {e}")
    except Exception as e:
        raise click.ClickException(
            f"Could not read or process key file {key_path}: {e}"
        )

    store = TrustedKeyStore(TRUSTED_KEYS_PATH)
    try:
        store.add(
            fingerprint=fpr,
            name=name,
            org=org or "",
            added_by=added_by,
            algo=detected_algo,
        )
        shutil.copy(key_path, keyring_dest_path)

        click.echo(f"✅ Trusted key entry added for '{name}'")
        click.echo(f"   ↳ Fingerprint: {fpr}")
        click.echo(f"   ↳ Key file stored in keyring: {keyring_dest_path}")

    except ValueError as e:
        raise click.ClickException(str(e))
    except (IOError, shutil.Error) as e:
        try:
            store.remove(fpr)
        except Exception:
            pass
        raise click.ClickException(f"Failed to copy key to keyring: {e}")


@trust_cmd.command("list")
@click.option("--json", "json_output", is_flag=True, help="Display keys in JSON format")
def list_cmd(json_output: bool):
    """List all trusted keys with names, organizations, and other metadata."""
    try:
        store = TrustedKeyStore(TRUSTED_KEYS_PATH)
    except ValueError as e:
        raise click.ClickException(f"Error loading trust store: {e}")

    keys = store.list_all()
    if not keys:
        click.echo("No trusted keys found.")
        return

    if json_output:
        click.echo(json.dumps(keys, indent=2))
    else:
        click.echo("🔐 Trusted keys:")
        for key_entry in sorted(keys, key=lambda x: x.get("fingerprint", "")):
            org_display = key_entry.get("org") or "N/A"
            click.echo(
                f" - {key_entry.get('name', 'N/A')} ({org_display}) : {key_entry.get('fingerprint', 'N/A')}"
            )


@trust_cmd.command("remove")
@click.argument("fingerprint")
def remove_cmd(fingerprint: str):
    """Remove a key from the trusted keys list by its fingerprint."""
    try:
        store = TrustedKeyStore(TRUSTED_KEYS_PATH)
        store.remove(fingerprint)
        click.echo(
            f"🗑️ Key entry removed from trust store for fingerprint: {fingerprint}"
        )
        click.echo(
            "   Note: The key file itself must be removed from the keyring directory manually."
        )
    except ValueError as e:
        raise click.ClickException(str(e))
    except IOError as e:
        raise click.ClickException(f"Failed to write to trust store: {e}")


@trust_cmd.command("update")
@click.argument("fingerprint")
@click.option(
    "--status",
    required=True,
    type=click.Choice(list(VALID_VERIFICATION_STATUSES)),
    help="New verification status.",
)
@click.option(
    "--updated-by", required=True, help="User or entity updating the key's status."
)
@click.option(
    "--notes",
    default=None,
    help="Optional notes for this status update (provide empty string '' to clear existing notes).",
)
def update_status_cmd(
    fingerprint: str, status: str, updated_by: str, notes: str | None
):
    """Update the verification status and notes of a trusted key."""
    try:
        store = TrustedKeyStore(TRUSTED_KEYS_PATH)
        store.update_verification_status(fingerprint, status, updated_by, notes)
        click.echo(f"✅ Key status updated for fingerprint: {fingerprint}")
    except ValueError as e:
        raise click.ClickException(str(e))
    except IOError as e:
        raise click.ClickException(f"Failed to write to trust store: {e}")
