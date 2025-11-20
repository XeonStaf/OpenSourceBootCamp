"""Утилита для отслеживания использования токенов из LLM ответов"""

from typing import Any, Dict, Optional


def extract_tokens_from_response(response: Any) -> Dict[str, int]:
    """
    Извлекает информацию о токенах из ответа LLM.
    
    Args:
        response: Ответ от LangChain LLM (может быть AIMessage, dict и т.д.)
    
    Returns:
        Dict с ключами: prompt_tokens, completion_tokens, total_tokens
    """
    tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    if response is None:
        return tokens
    
    try:
        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            if metadata:
                if isinstance(metadata, dict) and "token_usage" in metadata:
                    usage = metadata["token_usage"]
                    if isinstance(usage, dict):
                        tokens["prompt_tokens"] = usage.get("prompt_tokens", 0) or 0
                        tokens["completion_tokens"] = usage.get("completion_tokens", 0) or 0
                        tokens["total_tokens"] = usage.get("total_tokens", 0) or 0
                elif hasattr(metadata, "token_usage"):
                    usage = metadata.token_usage
                    if hasattr(usage, "prompt_tokens"):
                        tokens["prompt_tokens"] = getattr(usage, "prompt_tokens", 0) or 0
                        tokens["completion_tokens"] = getattr(usage, "completion_tokens", 0) or 0
                        tokens["total_tokens"] = getattr(usage, "total_tokens", 0) or 0
        
        if isinstance(response, dict):
            if "response_metadata" in response:
                metadata = response["response_metadata"]
                if isinstance(metadata, dict) and "token_usage" in metadata:
                    usage = metadata["token_usage"]
                    if isinstance(usage, dict):
                        tokens["prompt_tokens"] = usage.get("prompt_tokens", 0) or 0
                        tokens["completion_tokens"] = usage.get("completion_tokens", 0) or 0
                        tokens["total_tokens"] = usage.get("total_tokens", 0) or 0
            
            if "token_usage" in response:
                usage = response["token_usage"]
                if isinstance(usage, dict):
                    tokens["prompt_tokens"] = usage.get("prompt_tokens", 0) or 0
                    tokens["completion_tokens"] = usage.get("completion_tokens", 0) or 0
                    tokens["total_tokens"] = usage.get("total_tokens", 0) or 0
        
        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            tokens["prompt_tokens"] = getattr(usage, "prompt_tokens", 0) or 0
            tokens["completion_tokens"] = getattr(usage, "completion_tokens", 0) or 0
            tokens["total_tokens"] = getattr(usage, "total_tokens", 0) or 0
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Failed to extract tokens from response: {e}")
    
    return tokens


def add_tokens_to_statistics(
    task_details: Any, prompt_tokens: int, completion_tokens: int, total_tokens: int
) -> None:
    """
    Добавляет токены к общей статистике задачи.
    
    Args:
        task_details: Экземпляр TaskDetails
        prompt_tokens: Количество токенов в промпте
        completion_tokens: Количество токенов в ответе
        total_tokens: Общее количество токенов
    """
    if task_details:
        task_details.prompt_tokens += prompt_tokens
        task_details.completion_tokens += completion_tokens
        task_details.total_tokens += total_tokens

