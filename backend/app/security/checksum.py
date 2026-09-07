import hashlib
from pathlib import Path
from typing import Union

def compute_sha256(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file efficiently in chunks."""
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_sha256(file_path: Union[str, Path], expected_hash: str) -> bool:
    """Verify if the file matches the expected SHA-256 hash."""
    if not expected_hash:
        return False
    computed = compute_sha256(file_path)
    return computed.lower() == expected_hash.lower()

def compute_bytes_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of bytes in-memory."""
    return hashlib.sha256(data).hexdigest()
