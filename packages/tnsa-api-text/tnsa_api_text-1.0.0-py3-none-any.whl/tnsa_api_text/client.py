"""
Minimal TNSA API client for text generation
"""

import requests
from typing import Optional, List, Dict, Any, Union


class TNSA:
    """Minimal TNSA API client"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.tnsaai.com",
        timeout: float = 30.0
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def generate(
        self,
        prompt: str,
        model: str = "NGen3.9-Pro",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> Union[str, requests.Response]:
        """
        Generate text from prompt
        
        Args:
            prompt: Input text
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Return streaming response
            
        Returns:
            Generated text or streaming response
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "format": "html"
        }
        
        if stream:
            response = self.session.post(
                f"{self.base_url}/infer",
                json=payload,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()
            return response
        
        response = self.session.post(
            f"{self.base_url}/infer",
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("response", "")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "NGen3.9-Pro",
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Chat with messages
        
        Args:
            messages: List of {"role": "user/assistant", "content": "text"}
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Generated response text
        """
        # Convert messages to prompt
        prompt_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            elif role == "system":
                prompt_parts.append(f"System: {content}")
        
        prompt = "\n".join(prompt_parts) + "\nAssistant:"
        
        return self.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def models(self) -> List[str]:
        """Get available models"""
        response = self.session.get(f"{self.base_url}/models", timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("models", [])
    
    def close(self):
        """Close session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()