from langchain_openai import ChatOpenAI

from src.config.settings import LLM_SETTINGS

settings = LLM_SETTINGS

llm = ChatOpenAI(
    model=settings.LLM_NAME,
    verbose=True,
    base_url=settings.LLM_HOST,
    api_key=settings.API_KEY,
)
