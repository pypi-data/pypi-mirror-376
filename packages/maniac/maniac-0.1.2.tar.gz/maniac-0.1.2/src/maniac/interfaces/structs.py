"""Standard response models for AI providers"""

from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatCompletionMessage:
    """Message in a chat completion response"""
    role: str
    content: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class ChatCompletionChoice:
    """Choice in a chat completion response"""
    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[str] = None
    logprobs: Optional[Dict[str, Any]] = None


@dataclass
class Usage:
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatCompletionResponse:
    """Chat completion response matching OpenAI's format"""
    id: str
    object: str = "chat.completion"
    created: int = None
    model: str = None
    choices: List[ChatCompletionChoice] = None
    usage: Optional[Usage] = None
    system_fingerprint: Optional[str] = None
    
    def __post_init__(self):
        if self.created is None:
            self.created = int(datetime.now().timestamp())
        if self.choices is None:
            self.choices = []


@dataclass
class ChatCompletionChunk:
    """Streaming chat completion chunk"""
    id: str
    object: str = "chat.completion.chunk"
    created: int = None
    model: str = None
    choices: List[Dict[str, Any]] = None
    system_fingerprint: Optional[str] = None
    
    def __post_init__(self):
        if self.created is None:
            self.created = int(datetime.now().timestamp())
        if self.choices is None:
            self.choices = []
