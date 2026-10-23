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
