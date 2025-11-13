import asyncio

from tavily import AsyncTavilyClient

from src.config.search import search_settings
from src.config.settings import LLM_SETTINGS

tavily_client = AsyncTavilyClient(api_key=LLM_SETTINGS.TAVILY_API_KEY)


async def fetch_and_extract(queries):

    processed_queries = [
        {"query": query, "search_depth": "advanced", "max_results": search_settings.MAX_RESULTS} for query in queries
    ]

    responses = await asyncio.gather(*[tavily_client.search(**q) for q in processed_queries])

    relevant_urls = []
    for response in responses:
        for result in response.get("results", []):
            if result.get("score", 0) > search_settings.SEARCH_THRESHOLD:
                relevant_urls.append(result.get("url"))

    extracted_data = await asyncio.gather(*(tavily_client.extract(url) for url in relevant_urls))

    return extracted_data
