from pathlib import Path
import json
from datetime import datetime, timezone

VALID_VERIFICATION_STATUSES = {"pending", "verified", "revoked", "compromised"}
ACTIVELY_TRUSTED_STATUS = "verified"


class TrustedKeyStore:
    def __init__(self, trust_file: Path):
        """
        Initializes the trusted key store and loads the existing trusted keys from the trust file.
        :param trust_file: The path to the JSON file where trusted keys are stored.
        """
        self.trust_file = trust_file.resolve()
        self.trusted_keys: list[dict] = []

        self.trust_file.parent.mkdir(parents=True, exist_ok=True)
        self.load()

    def load(self):
        """Load trusted keys from the JSON file."""
        if self.trust_file.exists() and self.trust_file.stat().st_size > 0:
            try:
                with self.trust_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if (
                    isinstance(data, dict)
                    and "trusted_keys" in data
                    and isinstance(data["trusted_keys"], list)
                ):
                    self.trusted_keys = data["trusted_keys"]
                else:
                    self.trusted_keys = []
            except json.JSONDecodeError as e:
                self.trusted_keys = []
                raise ValueError(
                    f"Error loading trusted keys: Invalid JSON in {self.trust_file}."
                ) from e
            except Exception as e:
                self.trusted_keys = []
                raise ValueError(f"Error loading trusted keys: {e}") from e
        else:
            self.trusted_keys = []

    def get_key_entry(self, fingerprint: str) -> dict | None:
        """
        Retrieve a key entry by its fingerprint.
        :param fingerprint: The fingerprint of the public key.
        :return: The key entry dictionary if found, else None.
        """
        for key_entry in self.trusted_keys:
            if key_entry.get("fingerprint") == fingerprint:
                return key_entry
        return None

    def is_fingerprint_present(self, fingerprint: str) -> bool:
        """
        Check if a key with the given fingerprint is present in the store, regardless of status.
        :param fingerprint: The fingerprint of the public key.
        :return: Boolean indicating whether the key is present.
        """
        return self.get_key_entry(fingerprint) is not None

    def is_fingerprint_actively_trusted(self, fingerprint: str) -> bool:
        """
        Check if a key with the given fingerprint is present AND its status is 'verified'.
        :param fingerprint: The fingerprint of the public key.
        :return: Boolean indicating whether the key is actively trusted.
        """
        key_entry = self.get_key_entry(fingerprint)
        if key_entry:
            return key_entry.get("verification_status") == ACTIVELY_TRUSTED_STATUS
        return False

    def add(
        self,
        fingerprint: str,
        name: str,
        org: str,
        added_by: str,
        algo: str = "Ed25519",
    ):
        """
        Add a trusted key to the store with necessary metadata.
        Initial status is 'pending'.
        :param fingerprint: The fingerprint of the public key.
        :param name: The name of the signer.
        :param org: The organization of the signer.
        :param added_by: The user who added the key.
        :param algo: The signature algorithm used (default: Ed25519).
        :raises ValueError: if fingerprint is already present.
        """
        if not fingerprint or not isinstance(fingerprint, str):
            raise ValueError("Fingerprint must be a non-empty string.")
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string.")
        if not org or not isinstance(org, str):
            raise ValueError("Organization must be a non-empty string.")
        if not added_by or not isinstance(added_by, str):
            raise ValueError("Added_by must be a non-empty string.")

        if self.is_fingerprint_present(fingerprint):
            raise ValueError(
                f"Fingerprint {fingerprint} is already in the trust store."
            )

        new_key_entry = {
            "fingerprint": fingerprint,
            "name": name,
            "org": org,
            "added_by": added_by,
            "added_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "algo": algo,
            "last_verified_at": None,
            "verified_by": None,
            "verification_status": "pending",
            "notes": "",
        }
        self.trusted_keys.append(new_key_entry)
        self.save()

    def remove(self, fingerprint: str):
        """
        Remove a trusted key from the store by its fingerprint.
        :param fingerprint: The fingerprint of the key to remove.
        :raises ValueError: if fingerprint is not found.
        """
        original_count = len(self.trusted_keys)
        self.trusted_keys = [
            key for key in self.trusted_keys if key.get("fingerprint") != fingerprint
        ]
        if len(self.trusted_keys) == original_count:
            raise ValueError(
                f"Key with fingerprint {fingerprint} not found in the trust store."
            )
        self.save()

    def update_verification_status(
        self, fingerprint: str, status: str, updated_by: str, notes: str | None = None
    ):
        """
        Update the verification status and related metadata of a trusted key.
        :param fingerprint: The fingerprint of the key to update.
        :param status: The new verification status (e.g., "verified", "revoked").
        :param updated_by: The user who verified or revoked the key.
        :param notes: Optional notes regarding this status change.
        :raises ValueError: if key not found or status is invalid.
        """
        if status not in VALID_VERIFICATION_STATUSES:
            raise ValueError(
                f"Invalid verification status '{status}'. Must be one of {VALID_VERIFICATION_STATUSES}."
            )

        key_entry = self.get_key_entry(fingerprint)
        if not key_entry:
            raise ValueError(
                f"Key with fingerprint {fingerprint} not found in the trust store."
            )

        key_entry["verification_status"] = status
        key_entry["last_verified_at"] = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        key_entry["verified_by"] = updated_by
        if notes is not None:
            key_entry["notes"] = notes
        elif "notes" not in key_entry:
            key_entry["notes"] = ""

        self.save()

    def save(self):
        """Save the current trusted keys to the file, ensuring atomic write if possible."""
        # Use a temporary file and rename for more atomic save
        temp_file_path = self.trust_file.with_suffix(self.trust_file.suffix + ".tmp")
        try:
            with temp_file_path.open("w", encoding="utf-8") as f:
                json.dump({"trusted_keys": self.trusted_keys}, f, indent=2)
            # On POSIX systems, os.rename is atomic. On Windows, it might not be if destination exists.
            # Path.replace() is generally preferred for cross-platform atomic rename/replace.
            temp_file_path.replace(self.trust_file)
        except Exception as e:
            if temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except OSError:
                    pass
            raise IOError(f"Error saving trusted keys to {self.trust_file}: {e}") from e

    def list_all(self) -> list[dict]:
        """
        List all trusted keys with additional metadata.
        :return: A list of trusted keys.
        """
        return sorted(self.trusted_keys, key=lambda x: x.get("fingerprint", ""))
