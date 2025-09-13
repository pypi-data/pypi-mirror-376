"""Chat completions interface for AI providers"""

import requests

from typing import Optional, Dict, Any, List, Union, AsyncIterator, Iterator
from maniac.interfaces.structs import ChatCompletionResponse, ChatCompletionChoice, ChatCompletionMessage, Usage

from maniac.inference.parse import get_args
from maniac.metadata import ManiacMetadata

class Completions:
    """Chat completions endpoint handler"""
    
    def __init__(self, api_key: str):
        self.maniac_api_key = api_key
        self.maniac_kwargs = {"task_label", "judge_prompt"}
        self.maniac_request_headers = ManiacMetadata.construct_maniac_request_headers(api_key)
    
    def _parse_response(self, response_data: Dict[str, Any]) -> ChatCompletionResponse:
        """Parse JSON response into ChatCompletionResponse object"""
        # Handle error responses by returning raw data (preserves OpenAI compatibility)
        if "error" in response_data:
            return response_data
        
        # Parse choices
        choices = []
        if "choices" in response_data:
            for choice_data in response_data["choices"]:
                message_data = choice_data.get("message", {})
                message = ChatCompletionMessage(
                    role=message_data.get("role", "assistant"),
                    content=message_data.get("content"),
                    function_call=message_data.get("function_call"),
                    tool_calls=message_data.get("tool_calls")
                )
                choice = ChatCompletionChoice(
                    index=choice_data.get("index", 0),
                    message=message,
                    finish_reason=choice_data.get("finish_reason"),
                    logprobs=choice_data.get("logprobs")
                )
                choices.append(choice)
        
        # Parse usage
        usage = None
        if "usage" in response_data:
            usage_data = response_data["usage"]
            usage = Usage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0)
            )
        
        # Create ChatCompletionResponse
        return ChatCompletionResponse(
            id=response_data.get("id", ""),
            object=response_data.get("object", "chat.completion"),
            created=response_data.get("created"),
            model=response_data.get("model"),
            choices=choices,
            usage=usage,
            system_fingerprint=response_data.get("system_fingerprint")
        )

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        stream: bool = False,
        response_format: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        user: Optional[str] = None,
        **kwargs
    ) -> Union[ChatCompletionResponse, Iterator[Dict[str, Any]]]:
        """
        On the surface, this function creates a completion for the input and
        returns it to the user. Underneath, it records the inputs, outputs,
        model id, and task id.
        """
        
        # Assert inference request has been tagged with a task label.
        assert 'task_label' in kwargs
        assert 'judge_prompt' in kwargs

        inference_kwargs = {k: v for k, v in get_args().items() if k not in self.maniac_kwargs}

        # Forward to supabase router (which tunnels to either openrouter or a performant open model).
        payload = {
            "task": {
                # Task metadata args.
                "label": kwargs["task_label"],
                "judge_prompts": kwargs["judge_prompt"]
                "model": model,
            },
            **inference_kwargs # Inference args.
        }
        
        try:
            r = requests.post(
                    ManiacMetadata.INFERENCE_URL, 
                    headers=self.maniac_request_headers,
                    json=payload)
            r.raise_for_status()
            
            # Parse successful response into ChatCompletionResponse object
            response_data = r.json()
            return self._parse_response(response_data)
            
        except requests.exceptions.HTTPError as e:
            # Return OpenAI-compatible error format for HTTP errors
            if r.status_code >= 400:
                try:
                    error_data = r.json()
                    return error_data  # Return raw error response (OpenAI compatible)
                except:
                    # Fallback for non-JSON error responses
                    return {
                        "error": {
                            "message": f"HTTP {r.status_code}: {r.reason}",
                            "type": "http_error",
                            "code": r.status_code
                        }
                    }
            raise
        except requests.exceptions.RequestException as e:
            # Return OpenAI-compatible error format for connection issues
            return {
                "error": {
                    "message": f"Request failed: {str(e)}",
                    "type": "request_error",
                    "code": None
                }
            }

        # Return base_client response.
        return response

class ChatCompletions:
    """Chat interface with completions endpoint"""
    
    def __init__(self, api_key: str):
        self.completions = Completions(api_key)
