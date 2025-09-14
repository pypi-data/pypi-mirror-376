import hashlib


def file_hash(data: bytes, algo="sha256") -> str:
    h = hashlib.new(algo)
    h.update(data)
    return h.hexdigest()
