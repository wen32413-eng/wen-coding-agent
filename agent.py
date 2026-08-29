import json
from collections import deque

from openai import OpenAI

from config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    MAX_STEPS,
    MAX_CONTEXT_STEPS,
)
from context_manager import ContextManager
from prompts import SYSTEM_PROMPT
from tools import TOOL_SCHEMAS, execute_tool


class CodingAgent:
    def __init__(self):
        client_args = {
            "api_key": LLM_API_KEY,
        }

        if LLM_BASE_URL:
            client_args["base_url"] = LLM_BASE_URL

        self.client = OpenAI(**client_args)

        self.recent_tool_calls = deque(maxlen=3)

    def call_model(self, messages):
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

        return response.choices[0].message

    def is_repeated_call(
        self,
        name,
        arguments,
    ):
        signature = json.dumps(
            {
                "name": name,
                "arguments": arguments,
            },
            sort_keys=True,
            ensure_ascii=False,
        )

        self.recent_tool_calls.append(signature)

        if len(self.recent_tool_calls) < 3:
            return False

        return len(set(self.recent_tool_calls)) == 1

    def run(self, task: str):
        # A new task should start with fresh loop-detection state.
        self.recent_tool_calls.clear()

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

        for step in range(1, MAX_STEPS + 1):
            print()
            print(f"[Step {step}/{MAX_STEPS}]")
            print(
                f"Context steps: "
                f"{context.step_count()}/{MAX_CONTEXT_STEPS}"
            )

            # ---------------------------------------------
            # 1. Ask model for the next action
            # ---------------------------------------------

            try:
                assistant_message = self.call_model(
                    context.get_messages()
                )

            except Exception as exc:
                result = (
                    "Agent stopped because the LLM request failed:\n"
                    f"{type(exc).__name__}: {exc}"
                )

                print(result)
                return result

            # ---------------------------------------------
            # 2. Serialize model response
            # ---------------------------------------------

            serialized_message = {
                "role": "assistant",
                "content": assistant_message.content,
            }

            if assistant_message.tool_calls:
                serialized_message["tool_calls"] = []

                for call in assistant_message.tool_calls:
                    serialized_message["tool_calls"].append(
                        {
                            "id": call.id,
                            "type": call.type,
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                    )

            # ---------------------------------------------
            # 3. No tools requested = final answer
            # ---------------------------------------------

            if not assistant_message.tool_calls:
                final_answer = (
                    assistant_message.content
                    or "Task completed."
                )

                print()
                print("=" * 60)
                print("FINAL")
                print("=" * 60)
                print(final_answer)

                return final_answer

            # ---------------------------------------------
            # 4. Execute requested tools
            # ---------------------------------------------

            tool_messages = []

            for tool_call in assistant_message.tool_calls:
                name = tool_call.function.name

                try:
                    arguments = json.loads(
                        tool_call.function.arguments or "{}"
                    )

                except json.JSONDecodeError as exc:
                    result = (
                        "ToolError: model generated invalid JSON "
                        f"arguments: {exc}"
                    )

                    tool_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )

                    continue

                print(f"Tool: {name}")

                print(
                    "Args:",
                    json.dumps(
                        arguments,
                        ensure_ascii=False,
                    ),
                )

                # -----------------------------------------
                # 5. Repeated call detection
                # -----------------------------------------

                if self.is_repeated_call(
                    name,
                    arguments,
                ):
                    result = (
                        "ToolError: identical tool call repeated "
                        "three times. Reconsider your approach."
                    )

                else:
                    result = execute_tool(
                        name,
                        arguments,
                    )

                print("Result:")
                print(result[:3000])

                if len(result) > 3000:
                    print(
                        "... [terminal output truncated]"
                    )

                tool_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

            # ---------------------------------------------
            # 6. Store one complete interaction block
            # ---------------------------------------------

            context.add_step(
                assistant_message=serialized_message,
                tool_messages=tool_messages,
            )

        final_answer = (
            f"Agent stopped after reaching "
            f"MAX_STEPS={MAX_STEPS}. "
            "The task may be incomplete."
        )

        print(final_answer)

        return final_answer