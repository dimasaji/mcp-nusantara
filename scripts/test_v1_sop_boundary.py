"""Run the P0 offline regression without production dotenv or home-directory I/O.

Package-level app.models imports Settings even when importing streaming/mock.
Suppress both dotenv and process-environment settings sources before collection;
use a temporary home for legacy memory singletons. No app startup is performed.
"""
from pathlib import Path
import os
import sys
import tempfile
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    'tests/test_v1_sop_boundary.py',
    'tests/test_v1_service_dialogue.py',
    'tests/test_sop_ingestion.py',
    'tests/test_phase2_hardening.py',
    'tests/test_v1_chat_history.py',
    'tests/test_effective_rag_profile.py',
    'tests/test_document_scope_v1.py',
]


def main():
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    sys.dont_write_bytecode = True
    from pydantic_settings.sources.providers.dotenv import DotEnvSettingsSource
    from pydantic_settings.sources.providers.env import EnvSettingsSource
    import dotenv
    import pytest

    def no_environment(_self):
        return {}

    protected_data = os.path.normcase(str(ROOT / 'data'))
    def prevent_production_reads(event, arguments):
        if event not in {'open', 'sqlite3.connect'} or not arguments or not isinstance(arguments[0], (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(arguments[0]))
        normalized = os.path.normcase(os.path.abspath(path))
        if path.name == '.env' or path.name.startswith('.env.'):
            raise RuntimeError('PRODUCTION_DOTENV_READ_FORBIDDEN')
        if normalized == protected_data or normalized.startswith(protected_data + os.sep):
            raise RuntimeError('PRODUCTION_DATA_ACCESS_FORBIDDEN')
    sys.addaudithook(prevent_production_reads)

    with tempfile.TemporaryDirectory(prefix='nusantara-p0-offline-') as temporary:
        with (patch.object(Path, 'home', return_value=Path(temporary)),
              patch.object(DotEnvSettingsSource, '_read_env_files', no_environment),
              patch.object(EnvSettingsSource, '_load_env_vars', no_environment),
              patch.object(dotenv, 'dotenv_values', return_value={})):
            return pytest.main(['-p', 'no:cacheprovider', '-o', 'addopts=',
                                '-q', '--tb=short', *TESTS])


if __name__ == '__main__':
    raise SystemExit(main())
