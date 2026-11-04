from functools import lru_cache
import os
import re
import threading
from datetime import datetime, timezone
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
    port: int = 8765
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
    _bootstrap_configuration: NusantaraConfig | None = PrivateAttr(default=None)
    _configuration_lock: object = PrivateAttr(default_factory=threading.RLock)
    _model_revision: int = PrivateAttr(default=0)
    _model_selected_at: str | None = PrivateAttr(default=None)
    _last_v1_execution: dict | None = PrivateAttr(default=None)
    _last_verified_execution: dict | None = PrivateAttr(default=None)

    def compose_configuration(self, *, config_file=None, dotenv_environment=None,
                              environment=None, overrides=None, project_root=None) -> NusantaraConfig:
        with self._configuration_lock:
            return self._compose_configuration(config_file=config_file, dotenv_environment=dotenv_environment,
                environment=environment, overrides=overrides, project_root=project_root)

    def _compose_configuration(self, *, config_file=None, dotenv_environment=None,
                               environment=None, overrides=None, project_root=None) -> NusantaraConfig:
        """Compose once on the existing owner, before constructing dependencies.

        Explicit bootstrap layers may be supplied before the first consumer.
        Bootstrap recomposition still requires a new boot. Operator model changes
        use select_operator_model to replace only the existing owner's LLM leaf.
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
        self._bootstrap_configuration = configuration
        return configuration

    def configuration_snapshot(self) -> tuple[NusantaraConfig, int]:
        """One atomic capture per request; already running requests keep this snapshot."""
        with self._configuration_lock:
            return self.effective_configuration, self._model_revision

    def select_operator_model(self, model: str, *, expected_revision: int,
                              validated_configuration: NusantaraConfig) -> tuple[NusantaraConfig, int]:
        """CAS after provider inventory validation. Process-local; no file persistence."""
        configuration, revision = self.configuration_snapshot()
        return self.select_operator_runtime(configuration.llm.provider, model,
            expected_revision=expected_revision, validated_configuration=validated_configuration)

    def configuration_for_operator_provider(self, provider: str) -> NusantaraConfig:
        """Return a validated candidate based on immutable bootstrap settings."""
        with self._configuration_lock:
            bootstrap = self._bootstrap_configuration or self.effective_configuration
            if provider == bootstrap.llm.provider:
                return bootstrap
            if provider == 'ollama':
                return bootstrap.with_operator_provider('ollama', bootstrap.llm.model,
                                                         ollama_base_url='http://127.0.0.1:11434')
            raise ConfigurationError('OPENROUTER_NOT_BOOTSTRAPPED')

    def select_operator_runtime(self, provider: str, model: str, *, expected_revision: int,
                                validated_configuration: NusantaraConfig) -> tuple[NusantaraConfig, int]:
        """Atomically select an inventoried provider/model for this process only."""
        if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}', model):
            raise ConfigurationError('INVALID_MODEL_SELECTION')
        with self._configuration_lock:
            current = self.effective_configuration
            if current.runtime.profile != 'NORMAL' or current.runtime.workers != 1:
                raise ConfigurationError('MODEL_CONTROL_SINGLE_NORMAL_WORKER_REQUIRED')
            if current is not validated_configuration or expected_revision != self._model_revision:
                raise ConfigurationError('MODEL_SELECTION_CONFLICT')
            bootstrap = self._bootstrap_configuration or current
            if provider == bootstrap.llm.provider:
                candidate = bootstrap
            elif provider == 'ollama':
                candidate = bootstrap.with_operator_provider('ollama', bootstrap.llm.model,
                                                              ollama_base_url='http://127.0.0.1:11434')
            else:
                raise ConfigurationError('OPENROUTER_NOT_BOOTSTRAPPED')
            replacement = candidate.with_operator_model(model)
            self._effective_configuration = replacement
            self.llm_provider = provider
            self.llm_base_url = replacement.llm.base_url
            self.llm_model = model  # keep legacy readers on the same Settings owner aligned
            self._model_revision += 1
            self._model_selected_at = datetime.now(timezone.utc).isoformat()
            return replacement, self._model_revision

    def model_control_status(self) -> dict:
        with self._configuration_lock:
            configuration = self.effective_configuration
            now = datetime.now(timezone.utc)
            verified = self._last_verified_execution
            fresh = bool(verified and verified['revision'] == self._model_revision
                         and verified['model'] == configuration.llm.model
                         and verified['provider'] == configuration.llm.provider
                         and 0 <= (now - datetime.fromisoformat(verified['timestamp'])).total_seconds() <= 300)
            return {'provider': configuration.llm.provider, 'model': configuration.llm.model,
                'selectable_providers': list(dict.fromkeys(((self._bootstrap_configuration or configuration).llm.provider,
                                                            'ollama'))),
                'revision': self._model_revision, 'selected_at': self._model_selected_at,
                'selection_source': 'OPERATOR' if self._model_selected_at else 'BOOTSTRAP',
                'consistency_scope': 'CURRENT_PROCESS_ONLY', 'process_id': os.getpid(),
                'availability': 'INFERENCE_OBSERVED' if fresh else 'NOT_VERIFIED',
                'status': 'INFERENCE_VERIFIED' if fresh else 'NOT_VERIFIED',
                'checked_at': now.isoformat(), 'verified_at': verified['timestamp'] if fresh else None,
                'verification_scope': 'CURRENT_MODEL_REVISION_PROCESS_300_SECONDS',
                'selection_enabled': configuration.runtime.profile == 'NORMAL' and configuration.runtime.workers == 1,
                'last_request': dict(self._last_v1_execution) if self._last_v1_execution else None}

    def record_v1_execution(self, *, revision: int, model: str, provider_status: str,
                            grounded: bool, stages: tuple[str, ...], execution_identity: dict | None = None) -> None:
        with self._configuration_lock:
            self._last_v1_execution = {'revision': revision, 'model': model,
                'provider_status': provider_status, 'grounded': grounded, 'stages': list(stages),
                'timestamp': datetime.now(timezone.utc).isoformat()}
            identity = execution_identity or {}
            current = self.effective_configuration
            if (revision == self._model_revision and current.llm.provider == provider_status
                    and model == current.llm.model and identity.get('process_id') == os.getpid()
                    and identity.get('provider_id') == provider_status
                    and identity.get('identity_status') == 'RUNTIME_CONFIRMED'
                    and identity.get('confirmation_source') == 'PROVIDER_RESPONSE'
                    and all(identity.get(key) == model for key in ('actual_model', 'payload_model', 'selected_model'))):
                self._last_verified_execution = {'revision': revision, 'model': model, 'provider': provider_status,
                    'timestamp': self._last_v1_execution['timestamp']}

    @property
    def effective_configuration(self) -> NusantaraConfig:
        return self.compose_configuration()

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
