from cryptography.exceptions import InvalidSignature
from sigmate.secops.keys import load_private_key_ed25519, load_public_key_ed25519
from typing import Optional


def sign_data(
    data: bytes, private_key_pem: bytes, password: Optional[bytes] = None
) -> bytes:
    private_key = load_private_key_ed25519(private_key_pem, password=password)
    return private_key.sign(data)


def verify_signature(data: bytes, signature: bytes, public_key_pem: bytes) -> bool:
    try:
        public_key = load_public_key_ed25519(public_key_pem)
        public_key.verify(signature, data)
        return True
    except InvalidSignature:
        return False
