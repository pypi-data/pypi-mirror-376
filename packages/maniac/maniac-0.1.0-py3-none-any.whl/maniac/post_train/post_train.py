"""Post-training interface for dataset upload and training initiation"""

import requests
from typing import Dict, Any, List, Optional, Union
from maniac.metadata import ManiacMetadata


class PostTrain:
    """
    PostTrain client class for handling post-training operations.
    Provides interface for uploading datasets and initiating training processes.
    
    Usage:
        post_train = PostTrain("your-maniac-api-key")
        response = post_train.register_completions(dataset, task_label="my_training_task")
    """
    
    def __init__(self, api_key: str):
        """Initialize PostTrain with API key"""
        self.maniac_api_key = api_key
        self.maniac_request_headers = ManiacMetadata.construct_maniac_request_headers(api_key)
        
    
    def register_completions(
        self,
        dataset: List[Dict[str, Any]], 
        *,
        task_label: str,
        judge_prompt: str,
        training_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Register completion dataset for training.
        
        Args:
            dataset: List of completion examples. Each example should contain:
                    - messages: List of conversation messages
                    - completion: Expected completion/response
                    - metadata: Optional metadata for the example
            task_label: Unique identifier for this training task
            judge_prompt: Evaluation criteria for model selection.
            model_name: Base model to fine-tune (optional, will use default)
            training_config: Training hyperparameters and configuration
            **kwargs: Additional training parameters
            
        Returns:
            Dict containing upload status and training job information
            
        Example dataset format:
            [
                {
                    "messages": [
                        {"role": "user", "content": "What is the capital of France?"},
                        {"role": "assistant", "content": "The capital of France is Paris."}
                    ],
                    "metadata": {"domain": "geography", "difficulty": "easy"}
                },
                ...
            ]
        """
        
        # Validate required parameters
        if not dataset:
            raise ValueError("Cannot register empty dataset.")
        
        if not task_label:
            raise ValueError("task_label is required")
        
        # Validate the dataset format and convert to input/output format.
        # For now, we will expect data to be in the form of chat completions. The supported
        # roles are "system", "user", and "assistant".
        converted_dataset = []
        try:
            for i, datapoint in enumerate(dataset):
                if not isinstance(datapoint, dict):
                    raise ValueError(f"Datapoint at index {i} is not a dictionary. Found: {type(datapoint).__name__}")
                
                if "messages" not in datapoint:
                    raise ValueError(f"Datapoint at index {i} missing 'messages' key")
                
                messages = datapoint["messages"]
                if not isinstance(messages, list):
                    raise ValueError(f"Messages at index {i} should be a list. Found: {type(messages).__name__}")
                
                if len(messages) == 0:
                    raise ValueError(f"Messages list at index {i} is empty")
                
                # Validate messages and ensure last message is from assistant
                for j, message in enumerate(messages):
                    if not isinstance(message, dict):
                        raise ValueError(f"Message {j} in datapoint {i} is not a dictionary. Found: {type(message).__name__}")
                    
                    if "role" not in message:
                        raise ValueError(f"Message {j} in datapoint {i} missing 'role' key")
                    
                    if "content" not in message:
                        raise ValueError(f"Message {j} in datapoint {i} missing 'content' key")
                    
                    role = message["role"]
                    if role not in {'system', 'user', 'assistant'}:
                        raise ValueError(f"Invalid role '{role}' in message {j} of datapoint {i}. Supported roles: system, user, assistant")
                
                # Ensure the last message is from assistant
                if messages[-1]["role"] != "assistant":
                    raise ValueError(f"Last message in datapoint {i} must be from assistant. Found: {messages[-1]['role']}")
                
                # Convert to input/output format
                input_messages = messages[:-1]  # All messages except the last one
                output_message = messages[-1]["content"]  # Final assistant message content
                
                # Extract system prompt if present
                system_prompt = None
                if messages and messages[0]["role"] == "system":
                    system_prompt = messages[0]["content"]
                
                converted_datapoint = {
                    "input": input_messages,
                    "output": output_message,
                    "system_prompt": system_prompt
                }
                
                # Preserve any additional metadata from original datapoint
                for key, value in datapoint.items():
                    if key != "messages":
                        converted_datapoint[key] = value
                
                converted_dataset.append(converted_datapoint)
        
        except (TypeError, AttributeError, KeyError) as e:
            # Format the expected structure nicely
            expected_format = """
Expected dataset format:
[
    {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"},
            {"role": "assistant", "content": "Paris is the capital of France."},
            {"role": "user", "content": "What about Germany?"},
            {"role": "assistant", "content": "Berlin is the capital of Germany."}
        ]
    },
    {
        "messages": [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "2+2 equals 4."},
            {"role": "user", "content": "And what about 3+3?"},
            {"role": "assistant", "content": "3+3 equals 6."}
        ]
    }
]

Your dataset format appears to be invalid. Error details: {error}

Supported message roles: system, user, assistant
Each datapoint must be a dictionary with a 'messages' key containing a list of message dictionaries.
Each message must have 'role' and 'content' keys. Each messages list must end with an assisstant 
line.
""".format(error=str(e))
            
            raise ValueError(expected_format)

        payload = {
            "task": {
                "label": task_label,
                "judge_prompt": judge_prompt,
                "initial_system_prompt": None, # This should be extracted by the dataset.
                "frontier_model": None, # User should specify a frontier model capable of generating this data.
                                        # This might be unknown, what do we do then?
                "max_tokens": None, # Thi should be determined during validation of the dataset format.
            },
            "data": converted_dataset
        }
        # raise NotImplementedError("Still need to construct appropriate data payload given a dataset.")

        try:
            resp = requests.post(
                ManiacMetadata.DATA_UPLOAD_URL,
                headers=self.maniac_request_headers,
                json=payload)
            resp.raise_for_status()
            result = upload_request.json()
        
        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors from Supabase endpoints
            error_response = {
                "status": "error",
                "error_type": "http_error",
                "status_code": e.response.status_code,
                "message": f"HTTP {e.response.status_code}: {e.response.reason}",
                "task_label": task_label
            }
            
            try:
                error_data = e.response.json()
                error_response["error_details"] = error_data
            except:
                pass
                
            return error_response
            
        except requests.exceptions.RequestException as e:
            # Handle connection and other request errors
            return {
                "status": "error",
                "error_type": "request_error", 
                "message": f"Request failed: {str(e)}",
                "task_label": task_label
            }
            
        except Exception as e:
            # Handle any other errors
            return {
                "status": "error",
                "error_type": "unknown_error",
                "message": f"Unexpected error: {str(e)}",
                "task_label": task_label
            }
    
