"""Callback для отслеживания использования токенов в LangChain"""

from typing import Any, Dict, List
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class TokenUsageCallback(BaseCallbackHandler):
    """Callback для сбора статистики использования токенов"""
    
    def __init__(self):
        super().__init__()
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Вызывается при завершении LLM вызова"""
        for generation in response.generations:
            for gen in generation:
                if hasattr(gen, "message") and hasattr(gen.message, "response_metadata"):
                    metadata = gen.message.response_metadata
                    if metadata and "token_usage" in metadata:
                        usage = metadata["token_usage"]
                        if isinstance(usage, dict):
                            self.token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0) or 0
                            self.token_usage["completion_tokens"] += usage.get("completion_tokens", 0) or 0
                            self.token_usage["total_tokens"] += usage.get("total_tokens", 0) or 0
    
    def get_token_usage(self) -> Dict[str, int]:
        """Возвращает собранную статистику токенов"""
        return self.token_usage.copy()
    
    def reset(self) -> None:
        """Сбрасывает статистику"""
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

