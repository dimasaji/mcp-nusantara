from functools import lru_cache
import os
from pathlib import Path
from typing import Optional
from dotenv import dotenv_values
from pydantic import PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.nusantara_config import ConfigurationError, NusantaraConfig, load_nusantara_config

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
    _effective_configuration: NusantaraConfig | None = PrivateAttr(default=None)

    def compose_configuration(self, *, config_file=None, dotenv_environment=None,
                              environment=None, overrides=None, project_root=None) -> NusantaraConfig:
        """Compose once on the existing owner, before constructing dependencies.

        Explicit bootstrap layers may be supplied before the first consumer.
        Reloading or changing the shared context requires a new application boot.
        Legacy Settings remains available to consumers outside the R1 scope.
        """
        if self._effective_configuration is not None:
            if any(value is not None for value in
                   (config_file, dotenv_environment, environment, overrides, project_root)):
                raise ConfigurationError('CONFIGURATION_ALREADY_COMPOSED')
            return self._effective_configuration
        root = Path(project_root) if project_root is not None else Path.cwd()
        if dotenv_environment is None:
            # Interpolation could resolve credentials into otherwise safe fields.
            dotenv_environment = dotenv_values(root / '.env', interpolate=False)
        configuration = load_nusantara_config(
            config_file=config_file, dotenv_environment=dotenv_environment,
            environment=os.environ if environment is None else environment,
            overrides=overrides, project_root=project_root,
        )
        self._effective_configuration = configuration
        return configuration

    @property
    def effective_configuration(self) -> NusantaraConfig:
        return self.compose_configuration()

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
