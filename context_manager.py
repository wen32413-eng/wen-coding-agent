class ContextManager:
    """
    Manage conversation history without breaking tool-call/tool-result pairs.

    The system prompt and original user task are always preserved.
    Older completed agent steps are discarded as whole blocks.
    """

    def __init__(
        self,
        system_prompt: str,
        user_task: str,
        max_steps: int = 8,
    ):
        self.base_messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_task,
            },
        ]

        # Each block represents one complete:
        # assistant tool call -> tool result(s)
        self.step_blocks = []

        self.max_steps = max_steps

    def add_step(
        self,
        assistant_message: dict,
        tool_messages: list,
    ):
        """
        Store a complete agent step.

        We deliberately keep the assistant tool-call message and all
        corresponding tool results together.
        """

        block = [assistant_message]
        block.extend(tool_messages)

        self.step_blocks.append(block)

        self._trim()

    def _trim(self):
        """
        Keep only the most recent N completed steps.

        Importantly, trimming happens at step boundaries rather than
        individual messages, so a tool result is never separated from
        its corresponding tool call.
        """

        if len(self.step_blocks) > self.max_steps:
            self.step_blocks = self.step_blocks[-self.max_steps:]

    def get_messages(self) -> list:
        """
        Build the message list sent to the model.
        """

        messages = list(self.base_messages)

        for block in self.step_blocks:
            messages.extend(block)

        return messages

    def step_count(self) -> int:
        return len(self.step_blocks)