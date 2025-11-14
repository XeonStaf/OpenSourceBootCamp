from pydantic_settings import BaseSettings


class SearchSettings(BaseSettings):
    MAX_RESULTS: int = 5
    SEARCH_THRESHOLD: float = 0.5
    MAX_LEN: int = 399


search_settings = SearchSettings()
