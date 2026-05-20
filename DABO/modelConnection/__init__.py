"""
Public package interface.

This file makes the important classes/functions importable directly
from the package folder.
"""

from .privatModelsInterface import (
    LocalModelConnection,
    Factory as LocalModelFactory,
)

from .cloudModelsInterface import (
    OpenAIConnection,
    AnthropicConnection,
    Factory as CloudModelFactory,
)

from .utils import get_or_save_api_key


__all__ = [
    "LocalModelConnection",
    "LocalModelFactory",
    "OpenAIConnection",
    "AnthropicConnection",
    "CloudModelFactory",
    "get_or_save_api_key",
]