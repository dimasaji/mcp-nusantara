"""MDE-02 isolated resolution evidence; never loads repository dotenv or DB."""
import ast
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.core.nusantara_config import load_nusantara_config


def main():
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / 'app/core/config.py').read_text())
    # Evaluate the actual class and imports, excluding get_settings()/singleton.
    nodes = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
             or isinstance(node, ast.ClassDef) and node.name == 'Settings']
    namespace = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'isolated_settings', 'exec'), namespace)
    settings_type = namespace['Settings']
    results = []
    with tempfile.TemporaryDirectory(prefix='mde02-resolution-') as directory:
        work = Path(directory)
        dotenv = work / '.env'
        dotenv.write_text('LLM_MODEL=fixture-dotenv\n', encoding='utf-8')
        with patch.dict(os.environ, {}, clear=True):
            assert settings_type(_env_file=None).llm_model == 'llama3.2:1b'
            assert settings_type(_env_file=dotenv).llm_model == 'fixture-dotenv'
            os.environ['LLM_MODEL'] = 'fixture-process'
            assert settings_type(_env_file=dotenv).llm_model == 'fixture-process'
            assert settings_type(_env_file=dotenv, llm_model='fixture-init').llm_model == 'fixture-init'
        results.append({'path': 'Settings', 'precedence': 'DEFAULT < DOTENV < PROCESS ENV < INIT',
                        'checks': 4, 'status': 'PASS_ISOLATED'})
        config_file = work / 'config.json'
        config_file.write_text(json.dumps({'llm': {'model': 'fixture-file'}, 'rag': {'top_k': 6}}))
        config = load_nusantara_config(config_file=config_file,
            environment={'LLM_MODEL': 'fixture-env', 'PORT': '8002'},
            overrides={'llm': {'model': 'fixture-explicit'}}, project_root=work)
        sources = {p.field: p.source for p in config.provenance}
        assert config.llm.model == 'fixture-explicit' and sources['llm.model'] == 'EXPLICIT'
        assert config.runtime.port == 8002 and sources['runtime.port'] == 'ENV'
        assert config.rag.top_k == 6 and sources['rag.top_k'] == 'FILE'
        assert config.llm.generation.max_tokens == 512 and sources['llm.generation.max_tokens'] == 'DEFAULT'
        assert all(p.status in {'UNWIRED', 'DECLARED_ONLY'} for p in config.provenance)
        assert not (work / 'data').exists()
        results.append({'path': 'NusantaraConfig', 'precedence': 'DEFAULT < FILE < SELECTED ENV < EXPLICIT',
                        'checks': 6, 'status': 'PASS_ISOLATED', 'runtime_activation': False})
    result = {'task_id': 'MDE-02-20261007', 'status': 'PASS_ISOLATED', 'checks': 10,
              'results': results, 'production_dotenv_read': False, 'database_opened': False,
              'worker_started': False, 'provider_called': False, 'live_values_verified': 0}
    (root / 'reports/MDE02_RESOLUTION_20261007.json').write_text(json.dumps(result, indent=2) + '\n')
    snapshot = load_nusantara_config(project_root=root)
    field_records = []
    def leaves(data, prefix=''):
        for key, value in data.items():
            name = f'{prefix}.{key}' if prefix else key
            if isinstance(value, dict):
                yield from leaves(value, name)
            else:
                yield name, value
    consumed = {
        'llm.provider': 'OllamaProvider profile guard',
        'llm.base_url': 'OllamaProvider constructor', 'llm.model': 'OllamaProvider constructor/payload',
        'llm.connection_timeout_s': 'OllamaProvider constructor',
        **{f'llm.generation.{f}': 'OllamaProvider._options' for f in ('context_length', 'max_tokens', 'temperature', 'top_p')},
        **{f'rag.{f}': 'RAG KB config' for f in ('top_k', 'chunk_size', 'chunk_overlap', 'reranker_enabled', 'reranker_model')},
        **{f'embedding.{f}': 'IndoBERTEmbeddingAdapter fixed-profile guard / KB config' for f in ('provider', 'model', 'dimension')},
        'embedding.timeout_s': 'IndoBERTClient constructor',
        'paths.worker': 'IndoBERTClient constructor', 'paths.worker_python': 'IndoBERTClient constructor',
        'knowledge.database': 'SQLiteVectorStore constructor', 'knowledge.store_backend': 'RAG KB config',
    }
    for name, value in leaves(snapshot.safe_dump()):
        field_records.append({'namespace': 'NusantaraConfig', 'field': name,
            'owner': 'app/core/nusantara_config.py', 'default': value,
            'source': 'DEFAULT < FILE < SELECTED ENV < EXPLICIT',
            'override': 'Explicit loader inputs; existing consumer/request precedence retained',
            'consumer': consumed.get(name),
            'consumption': 'OPT_IN_SOURCE_PATH; see focused integration evidence' if name in consumed else 'DECLARATION_OR_VALIDATION_ONLY',
            'verified_live': False, 'compatibility_risk': 'Do not infer default API activation or authorization',
            'migration_requirement': 'None for KEEP; separate contract before default activation'})
    field_records.append({'namespace': 'NusantaraConfig', 'field': 'llm.auth_env_ref',
        'owner': 'app/core/nusantara_config.py', 'source': 'EXPLICIT reference only',
        'default': None, 'value_policy': 'Excluded from safe_dump/provenance/repr; never resolve credential',
        'consumer': None, 'consumption': 'DECLARATION_ONLY', 'verified_live': False,
        'compatibility_risk': 'Do not activate credential resolution', 'migration_requirement': 'Separate authorized secret boundary'})
    sites = []
    for path in sorted((root / 'app').rglob('*.py')):
        try:
            module = ast.parse(path.read_text(encoding='utf-8-sig'))
        except (SyntaxError, UnicodeError):
            continue
        for node in ast.walk(module):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'settings':
                sites.append({'kind': 'Settings', 'field': node.attr, 'file': path.relative_to(root).as_posix(), 'line': node.lineno})
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'os' and node.func.attr == 'getenv' and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                sites.append({'kind': 'ENV_IDENTIFIER_ONLY', 'field': node.args[0].value, 'file': path.relative_to(root).as_posix(), 'line': node.lineno})
    for name, info in settings_type.model_fields.items():
        consumers = [s for s in sites if s['kind'] == 'Settings' and s['field'] == name]
        field_records.append({'namespace': 'Settings', 'field': name, 'owner': 'app/core/config.py',
            'default': info.default, 'source': 'DEFAULT < DOTENV < PROCESS ENV < INIT',
            'override': 'Init arguments or environment before cached singleton construction; API request model override',
            'consumer': consumers, 'consumption': 'STATIC_READ_SITE' if consumers else 'NO_DIRECT_READ_IN_THIS_SCAN',
            'verified_live': False, 'compatibility_risk': 'Settings declarations differ from actual RAG profile/startup literals',
            'migration_requirement': 'Keep existing consumer semantics; no universal normalization'})
    mapping = {'task_id': 'MDE-02-20261007', 'scope': 'Central fields and actual direct app source read sites; no dynamic dataflow claim',
        'field_count': len(field_records), 'fields': field_records, 'read_sites': sites,
        'composition_entrypoint': 'app/main.py',
        'delegated_assembly': ['app/api/routes.py', 'app/api/v2_routes.py', 'app/knowledge/engine.py', 'app/knowledge/rag.py', 'app/hermes/agent.py'],
        'default_api_snapshot_loading': False, 'default_gateway_executor_activation': False,
        'effective_configuration': {'representation': 'DESIGN_ONLY', 'configured': 'Selected input/default',
            'resolved': 'Validated snapshot', 'consumed': 'Instance/request-bound execution evidence',
            'verified_live': 'Same-build running service/model/index evidence', 'live_values_verified': 0},
        'runtime_change': 'KEEP', 'precedence_changed': [], 'source_map_limit': 'Bare settings attributes and literal os.getenv; aliases, dynamic/indirect forwarding require constructor/tests/document evidence'}
    (root / 'reports/MDE02_CONFIGURATION_MAP_20261007.json').write_text(json.dumps(mapping, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
