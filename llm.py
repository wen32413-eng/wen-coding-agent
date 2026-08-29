from openai import OpenAI


class LLMClient:
    """
    OpenAI-compatible model boundary.

    Agent logic depends only on chat(), not on provider-specific
    configuration or SDK details.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str | None,
        model: str,
    ):
        client_args = {
            "api_key": api_key,
        }

        if base_url:
            client_args["base_url"] = base_url

        self.client = OpenAI(**client_args)
        self.model = model

    def chat(
        self,
        messages: list[dict],
        tools: list[dict],
    ):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        if not response.choices:
            raise RuntimeError(
                "LLM returned no response choices."
            )

        return response.choices[0].message