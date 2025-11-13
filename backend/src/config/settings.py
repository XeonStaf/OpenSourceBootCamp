from pathlib import Path
import sys

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    LLM_NAME: str | None = None
    LLM_HOST: str | None = None
    API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
    )

    @model_validator(mode="after")
    def _ensure_values_present(self):
        missing = [
            name
            for name, value in (
                ("LLM_NAME", self.LLM_NAME),
                ("LLM_HOST", self.LLM_HOST),
                ("API_KEY", self.API_KEY),
            )
            if not value
        ]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(
                "Please set : "
                f"{joined}"
            )
        return self


try:
    LLM_SETTINGS = LLMSettings()
except ValueError as error:
    sys.exit(f"Missing .env configuration! \n{error}")
