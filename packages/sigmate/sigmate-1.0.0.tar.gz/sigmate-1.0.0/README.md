<div align="center">
  <a href="https://github.com/opensecurity/sigmate-py">
    </a>
  <h1 align="center">sigmate</h1>
  <p align="center">
    A modern, developer-focused CLI for cryptographic file signing and verification.
    <br />
    <a href="#-key-features"><strong>Explore the features »</strong></a>
    <br />
    <br />
    <a href="https://github.com/opensecurity/sigmate-py/issues/new?template=bug_report.md">Report Bug</a>
    ·
    <a href="https://github.com/opensecurity/sigmate-py/issues/new?template=feature_request.md">Request Feature</a>
  </p>
</div>

<div align="center">
  <img src="https://img.shields.io/pypi/v/sigmate.svg?style=for-the-badge&logo=pypi&color=blue" alt="PyPI Version">
  <img src="https://img.shields.io/github/license/opensecurity/sigmate?style=for-the-badge&color=blue" alt="License">
  <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge" alt="Code Style: Black">
</div>

---

## About The Project

**`sigmate`** provides a fast, understandable, and secure workflow for signing and verifying files. Built for developers, release managers, and security teams, it replaces the complex and often opaque processes of tools like GPG with a streamlined, modern alternative based on Ed25519 cryptography.

The core philosophy is simple: signing should be easy, verification should be trustworthy, and the metadata accompanying a signature should be as valuable as the signature itself. `sigmate` generates structured, auditable artifacts that integrate seamlessly into CI/CD pipelines and supply chain security workflows.

### Why sigmate?

* **Developer-Focused:** Simple, intuitive commands and a configuration model that feels familiar.
* **Transparent & Auditable:** Generates human-readable JSON metadata and CycloneDX-compatible SBOMs alongside raw signatures.
* **Modern Cryptography:** Uses the fast and secure Ed25519 signature algorithm by default.
* **Decoupled Trust:** Manages a local "keyring" for convenience and a separate "trust store" for auditable policy, preventing accidental trust and enhancing security.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* `pip` and `pipx` (recommended)

### Installation

The recommended way to install `sigmate` is using `pip`, which ensures the tool and its dependencies are isolated from other Python projects.

```bash
pipx install sigmate
````

Alternatively, for development:

```bash
# Clone the repository
git clone https://github.com/opensecurity/sigmate-py.git
cd sigmate

# Install with Poetry
poetry install
```

### First-Time Configuration

Before you start signing, run the interactive `configure` command to set up your default identity and key paths. This is a one-time setup.

```bash
sigmate configure
```

This will prompt you for:

1.  **Your default private key** used for signing.
2.  **Your default signer identity** (it will try to detect this from your git configuration).
3.  The location of your **public key keyring**, where keys of other trusted signers will be stored.

-----

## Core Concepts

`sigmate` manages four key artifacts:

| Artifact                  | Location (Default)                      | Purpose                                                                                |
| ------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------- |
| **Signature** (`.sig`)    | `./signatures/`                         | The raw, binary Ed25519 signature. Provides cryptographic proof of authenticity.       |
| **Metadata** (`.meta.json`) | `./signatures/sigmate.meta.json`        | A JSON "receipt" for each signing operation, detailing who, what, when, and how.         |
| **Keyring** | `~/.config/sigmate/keys/`               | A directory of named `.pub` files for trusted public keys, used for convenient verification. |
| **Trust Store** | `~/.config/sigmate/trusted_...json`     | An audit log of which key fingerprints are trusted, by whom, and with what status.       |

-----

## Usage

### 1. Signing Files

The `sign` command generates cryptographic signatures and metadata for your files.

```bash
# Sign an entire directory, creating both .sig and .meta.json files
sigmate sign --walk ./my-project --both

# Sign a single file with an expiration of 72 hours
sigmate sign --file ./release.zip --expires-in 72 --both

# Sign files and generate a CycloneDX SBOM for supply chain security
sigmate sign --walk ./app --both --sbom
```

### 2. Trusting Other Signers

Before you can verify a signature from someone else, you must explicitly add their public key to your keyring and trust store.

```bash
# Add Alice's public key, give it the name "alice", and record that you added it
sigmate trust add /path/to/alice.pem --name alice --added-by "Your Name"

# Later, update the status of Alice's key to 'verified' after vetting her identity
sigmate trust update <alice_fingerprint> --status verified --updated-by "Your Name"
```

### 3. Verifying Signatures

The `verify` command checks the integrity and authenticity of files.

```bash
# Verify a directory using the key of a trusted signer from your keyring
sigmate verify --walk ./downloaded-project --signer alice

# Verify a single file using a specific public key file
sigmate verify --file important.dat --key /path/to/key.pem

# Get a machine-readable JSON report of the verification
sigmate verify --walk ./app --signer alice --json
```

-----

## Command Reference

### `sigmate sign`

  * **Target:** Specify files with `<path>`, `--walk <dir>`, or `--list <file>`.
  * **Output Types:**
      * `--raw`: Creates individual `.sig` files.
      * `--meta`: Creates a central `sigmate.meta.json`.
      * `--both`: Creates both raw and meta artifacts.
  * **Key Options:**
      * `--key <path>`: Path to the private key (overrides configured default).
      * `--identity "Name <email>"`: Signer identity (overrides configured default).
      * `--output <dir>`: Specify a custom output directory for artifacts.
      * `--no-abspath`: Store relative paths in metadata for portability.

### `sigmate verify`

  * **Target:** Specify files with `<path>`, `--walk <dir>`, or `--list <file>`.
  * **Key Source (choose one):**
      * `--key <path>`: Use a public key from a specific file path.
      * `--signer <name>`: Use a public key from your keyring by its trusted name.
  * **Key Options:**
      * `--require-trusted`: Fail verification if the signer's key is not marked as 'verified' in the trust store.
      * `--sig-type [raw|meta|auto]`: Specify which signature artifact to use.
      * `--json`: Output a machine-readable JSON report.

### `sigmate trust`

  * `add <keyfile> --name <alias>`: Adds a key to the trust store and keyring.
  * `list`: Shows all keys in the trust store.
  * `update <fingerprint> --status <status>`: Changes the verification status of a key (e.g., to `verified` or `revoked`).
  * `remove <fingerprint>`: Removes a key from the trust store.

### `sigmate configure`

  * Run interactively to set up default configuration values (private key, identity, keyring path).
  * Run with arguments (`--private-key-path ...`) to set values non-interactively for scripting.

### `sigmate clean`

  * `clean`: Removes default artifacts (`./signatures/`, checksum files) from the current directory.
  * `clean <path>`: Removes all contents of a specified artifact directory.

-----

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Please see the `CONTRIBUTING.md` file for details on our code of conduct, and the process for submitting pull requests to us.

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Authors
Lucian BLETAN --> Init python project

## Sigmate rust lang
[sigmate](https://github.com/opensecurity/sigmate)

## Contact

Project Link: [sigmate-py](https://github.com/opensecurity/sigmate-py)
