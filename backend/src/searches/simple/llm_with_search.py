import datetime

from langchain.agents import create_agent
from langchain_tavily import TavilySearch

from src.config.settings import LLM_SETTINGS
from src.models.llm import llm

settings = LLM_SETTINGS

tavily_search = TavilySearch(
    tavily_api_key=settings.TAVILY_API_KEY, max_results=settings.TAVILY_MAX_RESULTS, topic="general"
)


llm_with_search = create_agent(
    model=llm,
    tools=[tavily_search],
    system_prompt=f"""You are a helpful research assistant. Today's date is {datetime.date.today().strftime('%B %d, %Y')}. Use web search to find relevant
    information, then extract detailed content from the most promising sources to provide
    comprehensive insights.""",
)
