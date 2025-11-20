from pydantic_settings import BaseSettings


class SearchSettings(BaseSettings):
    MAX_RESULTS: int = 3
    SEARCH_THRESHOLD: float = 0.5
    MAX_LEN: int = 399
    MAX_EXTRACTED_URLS: int = 10
    MAX_TEXT_SETS_FOR_FACTS: int = 10


search_settings = SearchSettings()
