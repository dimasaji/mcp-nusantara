from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=False, extra='ignore')
    app_name: str = 'Nusantara Core + Hermes'
    app_version: str = '0.1.0'
    debug: bool = False
    host: str = '127.0.0.1'
    port: int = 8000
    llm_provider: str = 'ollama'
    llm_base_url: str = 'http://localhost:11434'
    llm_api_key: Optional[str] = None
    llm_model: str = 'llama3.2:1b'
    llm_context_tokens: int = 4096
    context_window_size: int = 10
    session_timeout_minutes: int = 30
    embedding_model: str = 'local-hash'
    vector_store_type: str = 'memory'
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_top_k: int = 5
    privacy_filter_enabled: bool = True
    log_level: str = 'INFO'

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
