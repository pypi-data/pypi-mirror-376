"""ManiacMetadata - Static configuration and constants for Maniac client"""

from dataclasses import dataclass
from typing import List


class ManiacMetadata:
    """Static metadata and configuration for Maniac inference client"""
    
    SUPPORTED_BASE_MODELS: List[str] = [
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "google/gemma-3-12b-pt",
        "openai/gpt-oss-20b",
        "Qwen/Qwen2.5-14B-Instruct",
        "unsloth/phi-4"
    ]
    
    SUPABASE_URL: str = "https://brquhbknccsztsatqlou.supabase.co"
    SUPABASE_ANON_KEY: str = "sb_publishable_QKUGToyhQqrn3yKJtKdEFg_HfTinnEZ"
    MANIAC_API_URL: str = "https://api.maniac.ai/functions/v1" 
    
    INFERENCE_URL: str = f"{MANIAC_API_URL}/inference"
    DATA_UPLOAD_URL: str = f"{MANIAC_API_URL}/direct-insert"
    
    @staticmethod
    def construct_maniac_request_headers(maniac_api_key: str):
        return {
            "Authorization": f"Bearer {ManiacMetadata.SUPABASE_ANON_KEY}",
            "apikey": ManiacMetadata.SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
            "maniac-apikey": maniac_api_key
        }
