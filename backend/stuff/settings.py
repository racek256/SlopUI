from functools import lru_cache
from pathlib import Path
import yaml
from pydantic_settings import BaseSettings
 
BASE = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # secrets from .env
    SECRET: str
    OPENROUTER_API_KEY: str = ""
    TAVILY_API: str = ""
    EXA_API: str = ""
    # non-secret from .env + yaml
    DEMO_MODE: bool = False
    SEARCH_PROVIDER: str = "local"
    LOG_LEVEL: str = "INFO"

    models_config: dict = {"env_file": BASE.parent / ".env", "extra": "ignore"}

    # structured yaml loaded once
    allowed_models: list = []

    @classmethod
    def load(cls):
        s = cls()
        with open(BASE / "config.yaml") as f:
            s = yaml.safe_load(f)
            return s

@lru_cache

def get_settings():
    return Settings.load()
