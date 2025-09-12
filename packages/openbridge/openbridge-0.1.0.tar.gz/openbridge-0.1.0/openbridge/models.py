from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel


class ContentBlock(BaseModel):
    type: Literal["text"]
    text: str


class ToolUseBlock(BaseModel):
    type: Literal["tool_use"]
    id: str
    name: str
    input: Dict[str, Union[str, int, float, bool, dict, list]]


class ToolResultBlock(BaseModel):
    type: Literal["tool_result"]
    tool_use_id: str
    content: Union[str, List[Dict[str, Any]], Dict[str, Any], List[Any], Any]


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: Union[str, List[Union[ContentBlock, ToolUseBlock, ToolResultBlock]]]


class Tool(BaseModel):
    name: str
    description: Optional[str]
    input_schema: Dict[str, Any]


class MessagesRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[Union[str, Dict[str, str]]] = "auto"
