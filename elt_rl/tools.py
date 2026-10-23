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
