import subprocess
from pathlib import Path

from config import WORKSPACE, COMMAND_TIMEOUT


def safe_path(relative_path: str) -> Path:
    candidate = (WORKSPACE / relative_path).resolve()

    try:
        candidate.relative_to(WORKSPACE)
    except ValueError:
        raise PermissionError(
            f"Access outside workspace is forbidden: {relative_path}"
        )

    return candidate
def list_files(path: str = ".") -> str:
    try:
        target = safe_path(path)

        if not target.exists():
            return f"ToolError: path does not exist: {path}"

        if not target.is_dir():
            return f"ToolError: not a directory: {path}"

        lines = []

        for item in sorted(
            target.iterdir(),
            key=lambda x: (not x.is_dir(), x.name)
        ):
            relative = item.relative_to(WORKSPACE)

            if item.is_dir():
                lines.append(f"[DIR]  {relative}/")
            else:
                lines.append(f"[FILE] {relative}")

        if not lines:
            return "(empty directory)"

        return "\n".join(lines)

    except Exception as exc:
        return f"ToolError: {type(exc).__name__}: {exc}"
def read_file(path: str) -> str:
    try:
        target = safe_path(path)

        if not target.exists():
            return f"ToolError: file does not exist: {path}"

        if not target.is_file():
            return f"ToolError: not a file: {path}"

        text = target.read_text(encoding="utf-8")

        result = []

        for number, line in enumerate(text.splitlines(), start=1):
            result.append(f"{number:4d} | {line}")

        return "\n".join(result)

    except UnicodeDecodeError:
        return f"ToolError: file is not UTF-8 text: {path}"

    except Exception as exc:
        return f"ToolError: {type(exc).__name__}: {exc}"
def write_file(path: str, content: str) -> str:
    try:
        target = safe_path(path)

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        return (
            f"Successfully wrote {path}\n"
            f"Characters written: {len(content)}"
        )

    except Exception as exc:
        return f"ToolError: {type(exc).__name__}: {exc}"
def replace_in_file(path: str, old: str, new: str) -> str:
    try:
        target = safe_path(path)

        if not target.exists():
            return f"ToolError: file does not exist: {path}"

        text = target.read_text(encoding="utf-8")

        count = text.count(old)

        if count == 0:
            return (
                "ToolError: target text was not found. "
                "Read the file again before retrying."
            )

        if count > 1:
            return (
                f"ToolError: target text occurs {count} times. "
                "Replacement is ambiguous."
            )

        updated = text.replace(old, new, 1)

        target.write_text(updated, encoding="utf-8")

        return f"Successfully updated {path}"

    except Exception as exc:
        return f"ToolError: {type(exc).__name__}: {exc}"
DANGEROUS_COMMAND_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "shutdown",
    "reboot",
    "poweroff",
]


def run_command(command: str) -> str:
    try:
        lower_command = command.lower()

        for pattern in DANGEROUS_COMMAND_PATTERNS:
            if pattern.lower() in lower_command:
                return (
                    "ToolError: command blocked by safety policy: "
                    f"{command}"
                )

        result = subprocess.run(
            command,
            cwd=WORKSPACE,
            shell=True,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        return (
            f"Exit code: {result.returncode}\n\n"
            f"STDOUT:\n{stdout or '(empty)'}\n\n"
            f"STDERR:\n{stderr or '(empty)'}"
        )

    except subprocess.TimeoutExpired:
        return (
            f"ToolError: command exceeded timeout "
            f"({COMMAND_TIMEOUT} seconds)"
        )

    except Exception as exc:
        return f"ToolError: {type(exc).__name__}: {exc}"
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List files and directories inside a workspace directory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Directory path relative to workspace. "
                            "Use '.' for workspace root."
                        ),
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read a UTF-8 text file from the workspace."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "File path relative to workspace."
                        ),
                    }
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Create or completely overwrite a UTF-8 text file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "content": {
                        "type": "string",
                    },
                },
                "required": [
                    "path",
                    "content",
                ],
                "additionalProperties": False,
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "replace_in_file",
            "description": (
                "Replace one unique exact text block in a file. "
                "Prefer this for small code modifications."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "old": {
                        "type": "string",
                        "description": (
                            "Exact existing text to replace."
                        ),
                    },
                    "new": {
                        "type": "string",
                        "description": (
                            "Replacement text."
                        ),
                    },
                },
                "required": [
                    "path",
                    "old",
                    "new",
                ],
                "additionalProperties": False,
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Execute a shell command inside the project workspace. "
                "Useful for tests, builds, linters and inspection."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                    }
                },
                "required": [
                    "command",
                ],
                "additionalProperties": False,
            },
        },
    },
]
TOOL_FUNCTIONS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "replace_in_file": replace_in_file,
    "run_command": run_command,
}


def execute_tool(name: str, arguments: dict) -> str:
    function = TOOL_FUNCTIONS.get(name)

    if function is None:
        return f"ToolError: unknown tool: {name}"

    try:
        return function(**arguments)

    except TypeError as exc:
        return f"ToolError: invalid arguments: {exc}"

    except Exception as exc:
        return f"ToolError: {type(exc).__name__}: {exc}"