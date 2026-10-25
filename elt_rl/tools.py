import json
import posixpath
from typing import Annotated

from tinker_cookbook.tool_use import ToolResult, simple_tool_result, tool

MAX_OUTPUT_CHARS = 16384
WRITABLE_PREFIX = "elt/"


class ELTTools:
    def __init__(self, sandbox, command_timeout: int = 120):
        self._sandbox = sandbox
        self._command_timeout = command_timeout
        self.submitted = False

    @tool
    async def bash(
        self,
        command: Annotated[str, "The bash command to execute in the workspace."],
    ) -> ToolResult:
        """Run a shell command in the workspace. Use it to run the loader, dbt, python, and to inspect data."""
        r = await self._sandbox.run_command(
            command, timeout=self._command_timeout, max_output_bytes=MAX_OUTPUT_CHARS
        )
        return simple_tool_result(
            json.dumps(
                {"exit_code": r.exit_code, "stdout": r.stdout, "stderr": r.stderr}
            )
        )

    @tool
    async def read_file(
        self,
        path: Annotated[str, "Path relative to the workspace root, e.g. config.yaml"],
    ) -> ToolResult:
        """Read a text file from the workspace."""
        try:
            r = await self._sandbox.read_file(path, max_bytes=MAX_OUTPUT_CHARS)
        except ValueError as e:
            return simple_tool_result(f"error: {e}")
        return simple_tool_result(
            r.stdout if r.exit_code == 0 else f"error: {r.stderr}"
        )

    @tool
    async def write_file(
        self,
        path: Annotated[str, "Path under elt/, e.g. elt/sources.yaml"],
        content: Annotated[str, "Full file content to write."],
    ) -> ToolResult:
        """Write a file under elt/. Parent folders are created automatically."""
        clean = posixpath.normpath(path)
        if not clean.startswith(WRITABLE_PREFIX):
            return simple_tool_result(
                f"error: you may only write under {WRITABLE_PREFIX}"
            )
        try:
            await self._sandbox.write_file(clean, content)
        except ValueError as e:
            return simple_tool_result(f"error: {e}")
        return simple_tool_result(f"wrote {clean}")

    @tool
    async def submit(self) -> ToolResult:
        self.submitted = True
        return simple_tool_result("submitted", should_stop=True)
