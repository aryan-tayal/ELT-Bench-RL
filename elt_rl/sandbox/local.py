import asyncio
import os
import shutil
import signal
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    metrics: dict = field(default_factory=dict)


class LocalSandbox:
    def __init__(self, root=None):
        self.root = Path(root or tempfile.mkdtemp(prefix="elt_sbx_")).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    @property
    def sandbox_id(self) -> str:
        return self.root.name

    async def send_heartbeat(self, timeout: int = 30) -> None:
        pass

    async def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _resolve(self, path) -> Path:
        p = (self.root / path).resolve()
        if not p.is_relative_to(self.root):
            raise ValueError(f"path escapes sandbox: {path}")
        return p
