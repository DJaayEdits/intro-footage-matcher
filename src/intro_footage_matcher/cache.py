from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def source_fingerprint(path: str | Path) -> str:
    source = Path(path).expanduser().resolve()
    stat = source.stat()
    payload = {
        "path": str(source),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:20]


class StageCache:
    """Small atomic JSON cache keyed by explicit stage inputs."""

    FORMAT_VERSION = 1

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, stage: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in stage)
        return self.root / f"{safe}.json"

    def load(self, stage: str, inputs: dict[str, Any]) -> Any | None:
        path = self.path_for(stage)
        if not path.exists():
            return None
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if envelope.get("format_version") != self.FORMAT_VERSION:
            return None
        if envelope.get("inputs") != inputs:
            return None
        return envelope.get("data")

    def write(self, stage: str, inputs: dict[str, Any], data: Any) -> Path:
        target = self.path_for(stage)
        envelope = {
            "format_version": self.FORMAT_VERSION,
            "stage": stage,
            "inputs": inputs,
            "data": data,
        }
        fd, temp_name = tempfile.mkstemp(prefix=f".{target.stem}-", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(envelope, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
        except BaseException:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
            raise
        return target
