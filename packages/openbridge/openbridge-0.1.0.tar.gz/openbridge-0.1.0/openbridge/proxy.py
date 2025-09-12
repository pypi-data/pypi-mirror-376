import json
import uuid
from typing import List

from openai import OpenAI

from .models import Message, MessagesRequest, Tool


class AnthropicToOpenAIProxy:
    def __init__(
        self, openai_client: OpenAI, target_model: str, max_output_tokens: int = 16384
    ):
        self.client = openai_client
        self.target_model = target_model
        self.max_output_tokens = max_output_tokens

    def convert_messages(self, messages: List[Message]) -> List[dict]:
        """Convert Anthropic messages to OpenAI format."""
        result = []
        for msg in messages:
            if isinstance(msg.content, str):
                result.append({"role": msg.role, "content": msg.content})
            else:
                # Handle blocks
                content_text = ""
                tool_calls = []

                for block in msg.content:
                    if block.type == "text":
                        content_text += block.text
                    elif block.type == "tool_use":
                        tool_calls.append(
                            {
                                "id": block.id,
                                "type": "function",
                                "function": {
                                    "name": block.name,
                                    "arguments": json.dumps(block.input),
                                },
                            }
                        )
                    elif block.type == "tool_result":
                        result.append(
                            {
                                "role": "tool",
                                "content": str(block.content),
                                "tool_call_id": block.tool_use_id,
                            }
                        )

                if content_text or tool_calls:
                    openai_msg = {"role": msg.role, "content": content_text}
                    if tool_calls:
                        openai_msg["tool_calls"] = tool_calls
                    result.append(openai_msg)
        return result

    def convert_tools(self, tools: List[Tool]) -> List[dict]:
        """Convert Anthropic tools to OpenAI format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
            }
            for tool in tools
        ]

    async def process_request(self, request: MessagesRequest) -> dict:
        """Process request."""
        messages = self.convert_messages(request.messages)
        tools = self.convert_tools(request.tools) if request.tools else None
        max_tokens = min(
            request.max_tokens or self.max_output_tokens, self.max_output_tokens
        )

        kwargs = {
            "model": self.target_model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        completion = self.client.chat.completions.create(**kwargs)

        choice = completion.choices[0]
        msg = choice.message

        if msg.tool_calls:
            content = []
            for call in msg.tool_calls:
                content.append(
                    {
                        "type": "tool_use",
                        "id": call.id,
                        "name": call.function.name,
                        "input": json.loads(call.function.arguments),
                    }
                )
            stop_reason = "tool_use"
        else:
            content = [{"type": "text", "text": msg.content or ""}]
            stop_reason = "end_turn"

        return {
            "id": f"msg_{uuid.uuid4().hex[:12]}",
            "model": self.target_model,
            "role": "assistant",
            "type": "message",
            "content": content,
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {
                "input_tokens": completion.usage.prompt_tokens,
                "output_tokens": completion.usage.completion_tokens,
            },
        }
