from pathlib import Path
from sigmate.utils.files import is_binary
from datetime import datetime, timezone
from sigmate.config import SIGMATE_VERSION
from sigmate.utils.git import get_git_author
import uuid


def generate_sbom_entry(
    path: Path, fileinfo: dict, relpath: Path, include_abspath: bool = True
) -> dict:
    properties = [
        {
            "name": "sigmate:media.type",
            "value": "binary" if is_binary(path) else "text",
        },
        {"name": "sigmate:relpath", "value": str(relpath)},
    ]

    properties.append(
        {
            "name": "sigmate:abspath",
            "value": str(path.resolve()) if include_abspath else None,
        }
    )
    # Filter out properties with None values, if any backend schema dislikes nulls
    properties = [p for p in properties if p["value"] is not None]

    return {
        "type": "file",
        "bom-ref": str(relpath),
        "name": fileinfo.get("file"),
        "version": fileinfo.get("version"),
        "hashes": [{"alg": "SHA-256", "content": fileinfo.get("file_hash")}],
        "signatures": [
            {
                "algorithm": fileinfo.get("signature_algorithm"),
                "value": fileinfo.get("signature"),
            }
        ],
        "properties": properties,
    }


def build_cyclonedx_sbom(components: list) -> dict:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tools": [
                {
                    "vendor": "opensecurity",
                    "name": "sigmate",
                    "version": SIGMATE_VERSION,
                    "external_references": [
                        {
                            "url": "https://github.com/opensecurity/sigmate-py",
                            "type": "vcs",
                        },
                        {
                            "url": "https://github.com/opensecurity",
                            "type": "website",
                        },
                    ],
                }
            ],
            "authors": [{"name": get_git_author() or "Unknown Author"}],
        },
        "components": components,
    }
