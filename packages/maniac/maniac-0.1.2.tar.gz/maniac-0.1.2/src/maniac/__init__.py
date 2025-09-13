"""Maniac Inference - LLM wrapper for telemetry and model routing"""

__version__ = "0.1.0"

from .client import Maniac
from . import inference
from . import interfaces
from . import post_train

__all__ = [
    "Maniac", 
    "inference", 
    "interfaces",
    "post_train"
]
