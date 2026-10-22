import asyncio
import os
import shutil
import signal
import tempfile
from asyncio.subprocess import PIPE
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_MAX_OUTPUT = 16384

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

    async def run_command(
        self, command, workdir=None, timeout=60, max_output_bytes=None
    ):
        limit = max_output_bytes or DEFAULT_MAX_OUTPUT
        cwd = self.root if workdir is None else self._resolve(workdir)
        proc = await asyncio.create_subprocess_shell(
            command, cwd=cwd, stdout=PIPE, stderr=PIPE, start_new_session=True
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout)
        except asyncio.TimeoutError:
            os.killpg(proc.pid, signal.SIGKILL)
            await proc.communicate()
            return SandboxResult("", f"timed out after {timeout}s", 124)
        return SandboxResult(
            out[:limit].decode(errors="replace"),
            err[:limit].decode(errors="replace"),
            proc.returncode,
        )
