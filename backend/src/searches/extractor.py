import asyncio
import logging
from datetime import datetime

from tavily import AsyncTavilyClient

from src.config.search import search_settings
from src.config.settings import LLM_SETTINGS

logger = logging.getLogger(__name__)

tavily_client = AsyncTavilyClient(api_key=LLM_SETTINGS.TAVILY_API_KEY)


async def fetch_and_extract(queries, foreign_query: str = None, country: str = None):
    logger.info(f"[EXTRACTOR] Starting search for {len(queries)} queries")

    processed_queries = [
        {"query": query, "search_depth": "advanced", "max_results": search_settings.MAX_RESULTS} for query in queries
    ]

    if foreign_query:
        logger.info(f"[EXTRACTOR] Adding foreign query: {foreign_query[:100]}... (country: {country})")
        processed_foreign_query = [
            {
                "query": foreign_query,
                "search_depth": "advanced",
                "max_results": search_settings.MAX_RESULTS,
                "country": country,
            }
        ]
        processed_queries += processed_foreign_query

    logger.info(f"[EXTRACTOR] Executing {len(processed_queries)} Tavily search requests...")
    start_time = datetime.now()
    responses = await asyncio.gather(*[tavily_client.search(**q) for q in processed_queries])
    elapsed = (datetime.now() - start_time).total_seconds()
    total_results = sum(len(r.get("results", [])) for r in responses)
    logger.info(f"[EXTRACTOR] Search completed in {elapsed:.2f}s. Found {total_results} total results")

    relevant_urls = []
    for i, response in enumerate(responses, 1):
        results = response.get("results", [])
        relevant = [r for r in results if r.get("score", 0) > search_settings.SEARCH_THRESHOLD]
        logger.info(f"[EXTRACTOR] Query {i}: {len(relevant)}/{len(results)} results above threshold (score > {search_settings.SEARCH_THRESHOLD})")
        relevant_urls.extend([r.get("url") for r in relevant])

    if not relevant_urls:
        logger.warning(f"[EXTRACTOR] No relevant URLs found above threshold")
        return []

    relevant_urls = list(dict.fromkeys(relevant_urls))
    relevant_urls = relevant_urls[:search_settings.MAX_EXTRACTED_URLS]
    logger.info(f"[EXTRACTOR] Limited to {len(relevant_urls)} unique URLs (max: {search_settings.MAX_EXTRACTED_URLS})")

    logger.info(f"[EXTRACTOR] Extracting content from {len(relevant_urls)} URLs...")
    start_time = datetime.now()
    extracted_data = await asyncio.gather(*(tavily_client.extract(url) for url in relevant_urls))
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"[EXTRACTOR] Content extraction completed in {elapsed:.2f}s")

    return extracted_data
