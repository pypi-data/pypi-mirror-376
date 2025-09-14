import hashlib
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa, ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
from typing import Optional


def load_private_key_ed25519(
    pem_data: bytes, password: Optional[bytes] = None
) -> ed25519.Ed25519PrivateKey:
    """Loads an Ed25519 private key from PEM data, optionally with a password."""
    try:
        private_key = serialization.load_pem_private_key(pem_data, password=password)
    except TypeError:
        raise ValueError(
            "Private key is encrypted and requires a password, or the password provided was incorrect."
        )
    except Exception as e:
        raise ValueError(f"Failed to load private key: {e}") from e

    if not isinstance(private_key, ed25519.Ed25519PrivateKey):
        raise ValueError(
            "Loaded private key is not an Ed25519 key. Sigmate currently only supports Ed25519 for operations."
        )
    return private_key


def load_public_key_ed25519(pem_data: bytes) -> ed25519.Ed25519PublicKey:
    """
    Loads an Ed25519 public key from PEM data.
    Raises ValueError if the key is not an Ed25519 public key, as sigmate operations depend on it.
    """
    try:
        public_key = serialization.load_pem_public_key(pem_data)
    except Exception as e:
        raise ValueError(f"Failed to load PEM public key: {e}") from e

    if not isinstance(public_key, ed25519.Ed25519PublicKey):
        raise ValueError(
            "Public key is not an Ed25519 key. Sigmate currently only supports Ed25519 for verification operations."
        )
    return public_key


def get_public_key_algorithm_name(public_key: PublicKeyTypes) -> str:
    """Determines a common name for the public key's algorithm."""
    if isinstance(public_key, ed25519.Ed25519PublicKey):
        return "Ed25519"
    elif isinstance(public_key, rsa.RSAPublicKey):
        return "RSA"
    elif isinstance(public_key, ec.EllipticCurvePublicKey):
        return f"EC-{public_key.curve.name}"
    return "Unknown"


def extract_public_key_and_algo(
    key_pem: bytes, password: Optional[bytes] = None
) -> tuple[PublicKeyTypes, str]:
    """
    Extracts a public key object and its algorithm name from various PEM-encoded inputs.
    It can be a raw public key, a private key (public part is derived),
    or an X.509 certificate (public key is extracted).
    Returns a tuple (public_key_object, algorithm_name_string).
    """
    public_key_obj: PublicKeyTypes | None = None

    try:
        public_key_obj = serialization.load_pem_public_key(key_pem)
    except Exception:
        pass

    if public_key_obj is None:
        try:
            private_key = serialization.load_pem_private_key(key_pem, password=password)
            public_key_obj = private_key.public_key()
        except Exception:
            pass

    if public_key_obj is None:
        try:
            cert = x509.load_pem_x509_certificate(key_pem)
            public_key_obj = cert.public_key()
        except Exception as e:
            raise ValueError(
                "Unable to load a public key from the PEM data. "
                "Not recognized as a raw public key, private key, or X.509 certificate."
            ) from e

    if public_key_obj is None:
        raise ValueError(
            "Failed to extract public key from PEM data through any known method."
        )

    algo_name = get_public_key_algorithm_name(public_key_obj)
    return public_key_obj, algo_name


def extract_public_key_fingerprint_and_algo(
    key_pem: bytes,
    hash_algo_name: str = "sha256",
    password: Optional[bytes] = None,
) -> tuple[str, str]:
    """
    Extracts a public key fingerprint and the key's algorithm name from various PEM inputs.
    Returns (fingerprint_hex_string, algorithm_name_string).
    """
    public_key, key_algo_name = extract_public_key_and_algo(key_pem, password=password)

    if isinstance(public_key, ed25519.Ed25519PublicKey):
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
    else:
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    h = hashlib.new(hash_algo_name)
    h.update(pub_bytes)
    fingerprint = h.hexdigest()
    return fingerprint, key_algo_name


def extract_public_key_fingerprint(
    key_pem: bytes, algo: str = "sha256", password: Optional[bytes] = None
) -> str:
    """
    Extracts a fingerprint from a public key derived from various PEM inputs.
    This is a convenience wrapper around extract_public_key_fingerprint_and_algo
    for cases where only the fingerprint is needed.
    """
    fingerprint, _ = extract_public_key_fingerprint_and_algo(
        key_pem, algo, password=password
    )
    return fingerprint
