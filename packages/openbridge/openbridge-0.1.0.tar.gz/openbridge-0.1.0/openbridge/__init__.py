"""OpenBridge - API bridge for LLM compatibility."""

from .cli import create_app, main
from .models import (ContentBlock, Message, MessagesRequest, Tool,
                     ToolResultBlock, ToolUseBlock)
from .proxy import AnthropicToOpenAIProxy
from .templates import get_homepage_html

__version__ = "0.1.0"
__all__ = [
    "ContentBlock",
    "ToolUseBlock",
    "ToolResultBlock",
    "Message",
    "Tool",
    "MessagesRequest",
    "AnthropicToOpenAIProxy",
    "create_app",
    "main",
    "get_homepage_html",
]
