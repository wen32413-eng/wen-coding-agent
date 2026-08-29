import os
import shlex
import subprocess
from fnmatch import fnmatch
from pathlib import Path

from config import (
    WORKSPACE,
    COMMAND_TIMEOUT,
    MAX_READ_LINES,
    MAX_TREE_ENTRIES,
    MAX_SEARCH_RESULTS,
)


# ============================================================
# Project filtering
# ============================================================

IGNORED_DIRECTORIES = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
}


BINARY_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".rar",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".class",
    ".jar",
    ".pyc",
}


# ============================================================
# Path safety
# ============================================================

def safe_path(relative_path: str) -> Path:
    """
    Resolve a path under WORKSPACE.

    Paths escaping the workspace through '..' or symlinks are rejected.
    """

    candidate = (WORKSPACE / relative_path).resolve()

    try:
        candidate.relative_to(WORKSPACE)
    except ValueError:
        raise PermissionError(
            f"Access outside workspace is forbidden: {relative_path}"
        )

    return candidate


def _is_ignored_directory(path: Path) -> bool:
    return path.name in IGNORED_DIRECTORIES


def _iter_project_files(directory: Path):
    """
    Recursively yield project files while skipping noisy directories
    and symbolic links.
    """

    try:
        entries = sorted(
            directory.iterdir(),
            key=lambda item: (
                not item.is_dir(),
                item.name.lower(),
            ),
        )
    except (PermissionError, OSError):
        return

    for item in entries:
        if item.is_symlink():
            continue

        if item.is_dir():
            if _is_ignored_directory(item):
                continue

            yield from _iter_project_files(item)

        elif item.is_file():
            yield item


# ============================================================
# Directory tools
# ============================================================

def list_files(path: str = ".") -> str:
    """
    List one level of a workspace directory.
    """

    try:
        target = safe_path(path)

        if not target.exists():
            return f"ToolError: path does not exist: {path}"

        if not target.is_dir():
            return f"ToolError: not a directory: {path}"

        lines = []

        for item in sorted(
            target.iterdir(),
            key=lambda x: (
                not x.is_dir(),
                x.name.lower(),
            ),
        ):
            if item.is_symlink():
                continue

            if (
                item.is_dir()
                and item.name in IGNORED_DIRECTORIES
            ):
                continue

            relative = item.relative_to(WORKSPACE)

            if item.is_dir():
                lines.append(
                    f"[DIR]  {relative.as_posix()}/"
                )
            else:
                lines.append(
                    f"[FILE] {relative.as_posix()}"
                )

        if not lines:
            return "(empty directory)"

        return "\n".join(lines)

    except Exception as exc:
        return (
            f"ToolError: "
            f"{type(exc).__name__}: {exc}"
        )


def list_tree(
    path: str = ".",
    max_depth: int = 4,
) -> str:
    """
    Recursively inspect project structure up to max_depth.
    """

    try:
        target = safe_path(path)

        if not target.exists():
            return f"ToolError: path does not exist: {path}"

        if not target.is_dir():
            return f"ToolError: not a directory: {path}"

        if max_depth < 1:
            return "ToolError: max_depth must be at least 1"

        max_depth = min(max_depth, 8)

        lines = []
        entry_count = 0
        truncated = False

        root_relative = target.relative_to(WORKSPACE)

        root_name = (
            "."
            if str(root_relative) == "."
            else root_relative.as_posix()
        )

        lines.append(f"[ROOT] {root_name}")

        def walk(
            directory: Path,
            depth: int,
        ):
            nonlocal entry_count
            nonlocal truncated

            if depth >= max_depth:
                return

            try:
                entries = sorted(
                    directory.iterdir(),
                    key=lambda item: (
                        not item.is_dir(),
                        item.name.lower(),
                    ),
                )
            except (PermissionError, OSError):
                return

            for item in entries:
                if entry_count >= MAX_TREE_ENTRIES:
                    truncated = True
                    return

                if item.is_symlink():
                    continue

                if (
                    item.is_dir()
                    and item.name in IGNORED_DIRECTORIES
                ):
                    continue

                relative = item.relative_to(WORKSPACE)
                indent = "  " * (depth + 1)

                if item.is_dir():
                    lines.append(
                        f"{indent}[DIR] "
                        f"{relative.as_posix()}/"
                    )

                    entry_count += 1

                    walk(
                        item,
                        depth + 1,
                    )

                    if truncated:
                        return

                elif item.is_file():
                    lines.append(
                        f"{indent}[FILE] "
                        f"{relative.as_posix()}"
                    )

                    entry_count += 1

        walk(
            target,
            0,
        )

        if truncated:
            lines.append(
                f"... [tree truncated after "
                f"{MAX_TREE_ENTRIES} entries]"
            )

        return "\n".join(lines)

    except Exception as exc:
        return (
            f"ToolError: "
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================
# Search tool
# ============================================================

def search_text(
    query: str,
    path: str = ".",
    file_pattern: str = "*",
    case_sensitive: bool = False,
    max_results: int = MAX_SEARCH_RESULTS,
) -> str:
    """
    Search plain text across project files.

    This is intentionally a simple substring search rather than
    a semantic or regex search.
    """

    try:
        if not query:
            return "ToolError: query cannot be empty"

        target = safe_path(path)

        if not target.exists():
            return f"ToolError: path does not exist: {path}"

        max_results = max(
            1,
            min(
                max_results,
                MAX_SEARCH_RESULTS,
            ),
        )

        if target.is_file():
            files = [target]
        else:
            files = _iter_project_files(target)

        results = []

        needle = (
            query
            if case_sensitive
            else query.casefold()
        )

        for file_path in files:
            if file_path.suffix.lower() in BINARY_SUFFIXES:
                continue

            relative = file_path.relative_to(WORKSPACE)
            relative_string = relative.as_posix()

            if not (
                fnmatch(
                    file_path.name,
                    file_pattern,
                )
                or fnmatch(
                    relative_string,
                    file_pattern,
                )
            ):
                continue

            try:
                # Avoid unexpectedly loading huge generated files.
                if file_path.stat().st_size > 2_000_000:
                    continue

                text = file_path.read_text(
                    encoding="utf-8"
                )

            except (
                UnicodeDecodeError,
                PermissionError,
                OSError,
            ):
                continue

            for line_number, line in enumerate(
                text.splitlines(),
                start=1,
            ):
                haystack = (
                    line
                    if case_sensitive
                    else line.casefold()
                )

                if needle in haystack:
                    preview = line.strip()

                    if len(preview) > 240:
                        preview = (
                            preview[:240]
                            + "..."
                        )

                    results.append(
                        f"{relative_string}:"
                        f"{line_number}: "
                        f"{preview}"
                    )

                    if len(results) >= max_results:
                        return (
                            "\n".join(results)
                            + "\n"
                            + (
                                "... [search results "
                                "truncated]"
                            )
                        )

        if not results:
            return (
                f"No matches found for "
                f"{query!r}."
            )

        return "\n".join(results)

    except Exception as exc:
        return (
            f"ToolError: "
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================
# File reading
# ============================================================

def read_file(
    path: str,
    start_line: int = 1,
    end_line: int | None = None,
) -> str:
    """
    Read a bounded line range from a UTF-8 text file.
    """

    try:
        target = safe_path(path)

        if not target.exists():
            return f"ToolError: file does not exist: {path}"

        if not target.is_file():
            return f"ToolError: not a file: {path}"

        if target.suffix.lower() in BINARY_SUFFIXES:
            return (
                f"ToolError: binary file cannot "
                f"be read as text: {path}"
            )

        if start_line < 1:
            return (
                "ToolError: start_line must "
                "be at least 1"
            )

        text = target.read_text(
            encoding="utf-8"
        )

        lines = text.splitlines()

        if not lines:
            return "(empty file)"

        total_lines = len(lines)

        if start_line > total_lines:
            return (
                f"ToolError: start_line "
                f"{start_line} exceeds file length "
                f"{total_lines}"
            )

        if end_line is None:
            requested_end = total_lines
        else:
            if end_line < start_line:
                return (
                    "ToolError: end_line must be "
                    "greater than or equal to "
                    "start_line"
                )

            requested_end = min(
                end_line,
                total_lines,
            )

        actual_end = min(
            requested_end,
            start_line + MAX_READ_LINES - 1,
        )

        output = [
            (
                f"[Showing lines "
                f"{start_line}-{actual_end} "
                f"of {total_lines}]"
            )
        ]

        for number in range(
            start_line,
            actual_end + 1,
        ):
            output.append(
                f"{number:4d} | "
                f"{lines[number - 1]}"
            )

        if actual_end < requested_end:
            output.append(
                f"... [read truncated at "
                f"{MAX_READ_LINES} lines]"
            )

        return "\n".join(output)

    except UnicodeDecodeError:
        return (
            f"ToolError: file is not "
            f"UTF-8 text: {path}"
        )

    except Exception as exc:
        return (
            f"ToolError: "
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================
# File editing
# ============================================================

def write_file(
    path: str,
    content: str,
) -> str:
    """
    Create or overwrite a UTF-8 text file.
    """

    try:
        target = safe_path(path)

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content,
            encoding="utf-8",
        )

        return (
            f"Successfully wrote {path}\n"
            f"Characters written: {len(content)}"
        )

    except Exception as exc:
        return (
            f"ToolError: "
            f"{type(exc).__name__}: {exc}"
        )


def replace_in_file(
    path: str,
    old: str,
    new: str,
) -> str:
    """
    Replace exactly one unique text block.
    """

    try:
        target = safe_path(path)

        if not target.exists():
            return f"ToolError: file does not exist: {path}"

        if not target.is_file():
            return f"ToolError: not a file: {path}"

        text = target.read_text(
            encoding="utf-8"
        )

        count = text.count(old)

        if count == 0:
            return (
                "ToolError: target text was not found. "
                "Read the relevant file section again "
                "before retrying."
            )

        if count > 1:
            return (
                f"ToolError: target text occurs "
                f"{count} times. "
                "Replacement is ambiguous. "
                "Use a larger unique text block."
            )

        updated = text.replace(
            old,
            new,
            1,
        )

        target.write_text(
            updated,
            encoding="utf-8",
        )

        return (
            f"Successfully updated {path}"
        )

    except Exception as exc:
        return (
            f"ToolError: "
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================
# Command execution
# ============================================================

ALLOWED_EXECUTABLES = {
    "python",
    "python3",
    "pytest",
    "git",
    "node",
    "npm",
    "npx",
    "java",
    "javac",
    "gcc",
    "g++",
    "cmake",
    "ctest",
    "cargo",
    "go",
    "dotnet",
}


ALLOWED_GIT_SUBCOMMANDS = {
    "status",
    "diff",
    "log",
    "show",
}


def _parse_command(command: str) -> list[str]:
    """
    Parse a command without invoking a shell.

    Windows and POSIX quoting rules differ, so use a different
    shlex mode depending on the host platform.
    """

    args = shlex.split(
        command,
        posix=(os.name != "nt"),
    )

    if os.name == "nt":
        cleaned = []

        for arg in args:
            if (
                len(arg) >= 2
                and arg[0] == arg[-1]
                and arg[0] in {"'", '"'}
            ):
                arg = arg[1:-1]

            cleaned.append(arg)

        return cleaned

    return args


def run_command(command: str) -> str:
    """
    Execute an allowlisted development command inside WORKSPACE.

    shell=False prevents shell operators such as &&, |, > and ;
    from being interpreted by the operating-system shell.
    """

    try:
        if not command.strip():
            return "ToolError: empty command"

        try:
            args = _parse_command(command)

        except ValueError as exc:
            return (
                "ToolError: unable to parse command: "
                f"{exc}"
            )

        if not args:
            return "ToolError: empty command"

        executable = Path(
            args[0]
        ).name.lower()

        if executable.endswith(".exe"):
            executable = executable[:-4]

        if executable not in ALLOWED_EXECUTABLES:
            return (
                "ToolError: executable is not allowed: "
                f"{executable}"
            )

        if executable == "git":
            if len(args) < 2:
                return (
                    "ToolError: git subcommand "
                    "is required"
                )

            git_subcommand = args[1].lower()

            if (
                git_subcommand
                not in ALLOWED_GIT_SUBCOMMANDS
            ):
                return (
                    "ToolError: git subcommand "
                    "is not allowed: "
                    f"{git_subcommand}"
                )

        result = subprocess.run(
            args,
            cwd=WORKSPACE,
            shell=False,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        return (
            f"Exit code: {result.returncode}\n\n"
            f"STDOUT:\n"
            f"{stdout or '(empty)'}\n\n"
            f"STDERR:\n"
            f"{stderr or '(empty)'}"
        )

    except subprocess.TimeoutExpired:
        return (
            "ToolError: command exceeded timeout "
            f"({COMMAND_TIMEOUT} seconds)"
        )

    except FileNotFoundError as exc:
        return (
            "ToolError: executable not found: "
            f"{exc}"
        )

    except Exception as exc:
        return (
            f"ToolError: "
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================
# Tool schemas presented to the LLM
# ============================================================

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List one level of files and directories "
                "inside a workspace directory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Directory path relative "
                            "to workspace."
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
            "name": "list_tree",
            "description": (
                "Recursively inspect the project structure. "
                "Useful when first exploring an unfamiliar repository."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Directory path relative "
                            "to workspace."
                        ),
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": (
                            "Maximum recursive depth. "
                            "Usually 3 or 4 is sufficient."
                        ),
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "search_text",
            "description": (
                "Search for plain text across project files "
                "and return matching file paths and line numbers. "
                "Use this to locate symbols, functions, error messages, "
                "imports, TODOs, or identifiers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                    },
                    "path": {
                        "type": "string",
                        "description": (
                            "Search root relative to workspace."
                        ),
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": (
                            "Optional glob such as '*.py'. "
                            "Defaults to all text files."
                        ),
                    },
                    "case_sensitive": {
                        "type": "boolean",
                    },
                    "max_results": {
                        "type": "integer",
                    },
                },
                "required": [
                    "query",
                ],
                "additionalProperties": False,
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read a bounded line range from a UTF-8 "
                "text file in the workspace."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": (
                            "First line to read. "
                            "Line numbering starts at 1."
                        ),
                    },
                    "end_line": {
                        "type": "integer",
                        "description": (
                            "Last line to read. "
                            "Omit to read from start_line "
                            "toward the end, subject to the "
                            "configured line limit."
                        ),
                    },
                },
                "required": [
                    "path",
                ],
                "additionalProperties": False,
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Create or completely overwrite "
                "a UTF-8 text file."
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
                "Prefer this over rewriting an entire existing file "
                "when making a small code change."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "old": {
                        "type": "string",
                    },
                    "new": {
                        "type": "string",
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
                "Execute an approved development command "
                "inside the workspace. Useful for tests, "
                "builds, linters and program execution."
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


# ============================================================
# Tool router
# ============================================================

TOOL_FUNCTIONS = {
    "list_files": list_files,
    "list_tree": list_tree,
    "search_text": search_text,
    "read_file": read_file,
    "write_file": write_file,
    "replace_in_file": replace_in_file,
    "run_command": run_command,
}


def execute_tool(
    name: str,
    arguments: dict,
) -> str:
    function = TOOL_FUNCTIONS.get(name)

    if function is None:
        return (
            f"ToolError: unknown tool: {name}"
        )

    try:
        return function(**arguments)

    except TypeError as exc:
        return (
            f"ToolError: invalid arguments: {exc}"
        )

    except Exception as exc:
        return (
            f"ToolError: "
            f"{type(exc).__name__}: {exc}"
        )