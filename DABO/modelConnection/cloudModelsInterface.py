from openai import OpenAI
from enums import REASONING
from .utils import get_or_save_api_key
import consts


class OpenAIConnection:
    """connection into OpenAI services"""

    def __init__(self):
        api_key = get_or_save_api_key(consts.OPENAI_KEY)
        self.client = OpenAI(api_key=api_key)
        self.model_name = input("Model Name: ")

    def chat(self, input: list[dict[str, str]], reasoning: REASONING = REASONING.NONE, tools=None) -> str:
        kwargs = {
            "model": self.model_name,
            "input": input,
        }

        # Only send reasoning when needed.
        # Some OpenAI models do not accept reasoning.
        if reasoning != REASONING.NONE:
            kwargs["reasoning"] = {"effort": reasoning.value}

        if tools is not None:
            kwargs["tools"] = tools

        response = self.client.responses.create(**kwargs)

        if response.output_text == "":
            print("no response")
            return ""

        return response.output_text


class AnthropicConnection:
    pass


def Factory(connection: str = "openai"):
    modelConnection = {
        "openai": OpenAIConnection,
        "anthropic": AnthropicConnection,
    }

    if connection not in modelConnection:
        raise ValueError(f"Unknown cloud connection: {connection}")

    return modelConnection[connection]()