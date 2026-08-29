import json
from collections import deque

from config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    MAX_STEPS,
    MAX_CONTEXT_STEPS,
)

from context_manager import ContextManager
from llm import LLMClient
from prompts import SYSTEM_PROMPT
from runtime import (
    ToolResult,
    RunStats,
)
from tools import (
    TOOL_SCHEMAS,
    execute_tool,
)


class CodingAgent:
    def __init__(self):
        self.llm = LLMClient(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            model=LLM_MODEL,
        )

        self.recent_tool_calls = deque(
            maxlen=3
        )

    def is_repeated_call(
        self,
        name: str,
        arguments: dict,
    ) -> bool:
        signature = json.dumps(
            {
                "name": name,
                "arguments": arguments,
            },
            sort_keys=True,
            ensure_ascii=False,
        )

        self.recent_tool_calls.append(
            signature
        )

        if len(
            self.recent_tool_calls
        ) < 3:
            return False

        return (
            len(
                set(
                    self.recent_tool_calls
                )
            )
            == 1
        )

    def run(
        self,
        task: str,
    ):
        """
        Main agent loop:

        Task
          -> LLM
          -> Tool Call
          -> Local Execution
          -> Observation
          -> LLM
          -> ...
          -> Final Answer
        """

        self.recent_tool_calls.clear()

        stats = RunStats()

        context = ContextManager(
            system_prompt=SYSTEM_PROMPT,
            user_task=task,
            max_steps=MAX_CONTEXT_STEPS,
        )

        print()
        print("=" * 60)
        print("TASK")
        print("=" * 60)
        print(task)

        for step in range(
            1,
            MAX_STEPS + 1,
        ):
            stats.record_step(step)

            print()
            print(
                f"[Step {step}/{MAX_STEPS}]"
            )

            print(
                "Context steps: "
                f"{context.step_count()}/"
                f"{MAX_CONTEXT_STEPS}"
            )

            # ==================================================
            # 1. Ask model for next action
            # ==================================================

            try:
                assistant_message = (
                    self.llm.chat(
                        messages=(
                            context.get_messages()
                        ),
                        tools=TOOL_SCHEMAS,
                    )
                )

            except Exception as exc:
                final = (
                    "Agent stopped because "
                    "the LLM request failed:\n"
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

                print(final)
                stats.print_summary()

                return final

            # ==================================================
            # 2. Serialize model response for conversation
            # ==================================================

            serialized_message = {
                "role": "assistant",
                "content": (
                    assistant_message.content
                ),
            }

            if assistant_message.tool_calls:
                serialized_message[
                    "tool_calls"
                ] = []

                for call in (
                    assistant_message.tool_calls
                ):
                    serialized_message[
                        "tool_calls"
                    ].append(
                        {
                            "id": call.id,
                            "type": call.type,
                            "function": {
                                "name": (
                                    call.function.name
                                ),
                                "arguments": (
                                    call.function.arguments
                                ),
                            },
                        }
                    )

            # ==================================================
            # 3. No tool call => task complete
            # ==================================================

            if (
                not assistant_message.tool_calls
            ):
                final_answer = (
                    assistant_message.content
                    or "Task completed."
                )

                print()
                print("=" * 60)
                print("FINAL")
                print("=" * 60)
                print(final_answer)

                stats.print_summary()

                return final_answer

            # ==================================================
            # 4. Execute requested tools
            # ==================================================

            tool_messages = []

            for tool_call in (
                assistant_message.tool_calls
            ):
                name = (
                    tool_call.function.name
                )

                # ----------------------------------------------
                # Parse model-generated JSON arguments
                # ----------------------------------------------

                try:
                    arguments = json.loads(
                        tool_call.function.arguments
                        or "{}"
                    )

                except json.JSONDecodeError as exc:
                    tool_result = ToolResult(
                        ok=False,
                        text=(
                            "Model generated invalid "
                            "JSON arguments: "
                            f"{exc}"
                        ),
                    )

                    result_text = (
                        tool_result.to_model_text()
                    )

                    stats.record_tool(
                        name=name,
                        arguments={},
                        result=tool_result,
                    )

                    tool_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": (
                                tool_call.id
                            ),
                            "content": (
                                result_text
                            ),
                        }
                    )

                    continue

                print(
                    f"Tool: {name}"
                )

                print(
                    "Args:",
                    json.dumps(
                        arguments,
                        ensure_ascii=False,
                    ),
                )

                # ----------------------------------------------
                # Detect obvious repeated-action loops
                # ----------------------------------------------

                if self.is_repeated_call(
                    name,
                    arguments,
                ):
                    tool_result = ToolResult(
                        ok=False,
                        text=(
                            "Identical tool call was "
                            "repeated three times. "
                            "Reconsider the approach "
                            "using new evidence."
                        ),
                    )

                else:
                    tool_result = (
                        execute_tool(
                            name,
                            arguments,
                        )
                    )

                stats.record_tool(
                    name=name,
                    arguments=arguments,
                    result=tool_result,
                )

                result_text = (
                    tool_result.to_model_text()
                )

                status = (
                    "SUCCESS"
                    if tool_result.ok
                    else "ERROR"
                )

                print(
                    f"Result [{status}]:"
                )

                print(
                    result_text[:3000]
                )

                if (
                    len(result_text)
                    > 3000
                ):
                    print(
                        "... [terminal output "
                        "truncated]"
                    )

                tool_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": (
                            tool_call.id
                        ),
                        "content": (
                            result_text
                        ),
                    }
                )

            # ==================================================
            # 5. Store one complete interaction
            # ==================================================

            context.add_step(
                assistant_message=(
                    serialized_message
                ),
                tool_messages=(
                    tool_messages
                ),
            )

        # ======================================================
        # MAX_STEPS reached
        # ======================================================

        final_answer = (
            "Agent stopped after reaching "
            f"MAX_STEPS={MAX_STEPS}. "
            "The task may be incomplete."
        )

        print()
        print(final_answer)

        stats.print_summary()

        return final_answer