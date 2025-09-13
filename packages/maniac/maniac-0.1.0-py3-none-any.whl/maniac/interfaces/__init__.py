"""Generic AI provider interfaces"""

from .structs import ChatCompletionResponse, ChatCompletionMessage, ChatCompletionChoice, Usage

__all__ = [
    "ChatCompletionResponse", 
    "ChatCompletionMessage", 
    "ChatCompletionChoice",
    "Usage",
]
