import hashlib
from pathlib import Path


def sha1sum(path: Path, chunk_size: int = 8192) -> str:
    sha1 = hashlib.sha1()
    with path.open('rb') as f:
        while chunk := f.read(chunk_size):
            sha1.update(chunk)
    return sha1.hexdigest()