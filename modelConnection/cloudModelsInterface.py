from openai import OpenAI
from enum import Enum
from .utils import get_or_save_api_key
import consts


class OpenAIConnection:
    """connection into OpenAI services"""

    class REASONING(Enum):
        """reasoning type for OpenAI models"""
        NONE = "none"
        MINIMAL = "minimal"
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        XHIGH = "xhigh"

    def __init__(self):
        api_key = get_or_save_api_key(consts.OPENAI_KEY)
        self.client = OpenAI(api_key=api_key)
        self.model_name = input("Model Name: ")

    def chat(self, input: list[dict[str, str]], reasoning=None, tools=None) -> str:
        if reasoning is None:
            reasoning = self.REASONING.NONE

        kwargs = {
            "model": self.model_name,
            "input": input,
        }

        if reasoning != self.REASONING.NONE:
            kwargs["reasoning"] = {
                "effort": reasoning.value
            }

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