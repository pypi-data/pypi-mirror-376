"""Maniac inference client - Unified interface for AI providers with built-in telemetry"""

from maniac.inference.chat import ChatCompletions
from maniac.post_train import PostTrain
from maniac.metadata import ManiacMetadata

from supabase import create_client as sb_create_client, Client as SbClient

class Maniac:
    """
    Maniac inference client class. Unified interface for AI providers with built-in telemetry.

    Usage:
        client = Maniac("your-maniac-api-key")
        
        # Chat completions
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}],
            task_label="greeting"
        )
        
        # Post-training
        result = client.post_training.register_completions(
            dataset=[...],
            task_label="my_training_task"
        )
    """
    
    @property
    def supported_base_models(self):
        return ManiacMetadata.SUPPORTED_BASE_MODELS
    
    def __init__(self, api_key: str = None):
        self.maniac_api_key = api_key 
        self.supabase_user_key = api_key

        # Chat completions interface
        self.chat = ChatCompletions(api_key)
        
        # Post-training interface
        self.post_training = PostTrain(api_key)

        # Telemetry interface
        self.data_client = sb_create_client(ManiacMetadata.SUPABASE_URL, ManiacMetadata.SUPABASE_ANON_KEY)
