import hashlib
from pathlib import Path
from typing import Union
from volunteer_node.logger import logger

class SandboxSecurity:
    @staticmethod
    def compute_sha256(file_path: Union[str, Path]) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def verify_checksum(file_path: Union[str, Path], expected_hash: str) -> bool:
        if not expected_hash:
            return True
        computed = SandboxSecurity.compute_sha256(file_path)
        return computed.lower() == expected_hash.lower()

    @staticmethod
    def validate_safe_path(target_path: Union[str, Path], allowed_base_dir: Union[str, Path]) -> bool:
        """
        Prevent path traversal attacks (e.g. ../../../etc/passwd or /root escapes).
        Guarantees that target_path is strictly within allowed_base_dir.
        """
        base = Path(allowed_base_dir).resolve()
        target = Path(target_path).resolve()
        try:
            target.relative_to(base)
            return True
        except ValueError:
            logger.error(f"Security Alert: Path {target} escapes allowed sandbox directory {base}!")
            return False

sandbox_security = SandboxSecurity()
