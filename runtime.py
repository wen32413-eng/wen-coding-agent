from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """
    Structured result produced by local tool execution.
    """

    ok: bool
    text: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_model_text(self) -> str:
        status = (
            "SUCCESS"
            if self.ok
            else "ERROR"
        )

        return (
            f"STATUS: {status}\n"
            f"{self.text}"
        )


@dataclass
class RunStats:
    """
    Lightweight runtime statistics for one agent task.
    """

    steps: int = 0
    tool_calls: int = 0
    successful_tools: int = 0
    failed_tools: int = 0

    changed_files: set[str] = field(
        default_factory=set
    )

    commands: list[dict] = field(
        default_factory=list
    )

    def record_step(
        self,
        step: int,
    ):
        self.steps = max(
            self.steps,
            step,
        )

    def record_tool(
        self,
        name: str,
        arguments: dict,
        result: ToolResult,
    ):
        self.tool_calls += 1

        if result.ok:
            self.successful_tools += 1
        else:
            self.failed_tools += 1

        if (
            result.ok
            and name
            in {
                "write_file",
                "replace_in_file",
            }
        ):
            path = arguments.get("path")

            if path:
                self.changed_files.add(path)

        if name == "run_command":
            self.commands.append(
                {
                    "command": arguments.get(
                        "command",
                        "",
                    ),
                    "ok": result.ok,
                    "exit_code": (
                        result.metadata.get(
                            "exit_code"
                        )
                    ),
                }
            )

    def print_summary(self):
        print()
        print("=" * 60)
        print("RUN SUMMARY")
        print("=" * 60)

        print(
            f"Steps:             {self.steps}"
        )

        print(
            f"Tool calls:        {self.tool_calls}"
        )

        print(
            f"Successful tools:  "
            f"{self.successful_tools}"
        )

        print(
            f"Failed tools:      "
            f"{self.failed_tools}"
        )

        if self.changed_files:
            print(
                "Files changed:     "
                + ", ".join(
                    sorted(
                        self.changed_files
                    )
                )
            )
        else:
            print(
                "Files changed:     none"
            )

        if self.commands:
            last = self.commands[-1]

            status = (
                "PASSED"
                if last["ok"]
                else "FAILED"
            )

            print(
                f"Last command:      "
                f"{last['command']}"
            )

            print(
                f"Verification:      "
                f"{status}"
            )