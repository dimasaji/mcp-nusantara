"""Pure source/compiled-code comparison; never import or boot the application."""
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path
from types import CodeType

root=Path(r'C:\Users\dmaza\mcp-starter')
out=Path(__file__).resolve().parent
live=json.loads((out/'RESPONSE.json').read_text())['attestation']
before=json.loads((out/'PROCESS_BEFORE.json').read_text())
after=json.loads((out/'PROCESS_AFTER.json').read_text())
identity_source=root/'app/core/runtime_identity.py'
attestation_source=root/'app/core/runtime_attestation.py'
identity_tree=ast.parse(identity_source.read_text(encoding='utf-8-sig'))
attestation_tree=ast.parse(attestation_source.read_text(encoding='utf-8-sig'))
def extract(tree,name,filename,namespace):
    selected=[n for n in tree.body if isinstance(n,ast.ImportFrom) and n.module=='__future__']
    selected += [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len([n for n in selected if isinstance(n,ast.FunctionDef)])==1
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(filename),'exec'),namespace)
    return namespace[name]

# Same inspected source algorithm, with explicit file-safety precheck.
candidate=[p for p in (root/'app').rglob('*') if p.is_file() and p.suffix in {'.py','.json','.html','.css','.js'}]
candidate += [root/'pyproject.toml',root/'nusantara-models/indobert_worker.py']
for file in candidate:
    parts={p.lower() for p in file.relative_to(root).parts}
    if file.suffix=='.json' and parts.intersection({'knowledge','rag','data','index','indices','indexes'}):
        raise ValueError('UNSAFE_SOURCE_SNAPSHOT_INPUT')
source_build_id=extract(identity_tree,'source_build_id',identity_source,{'Path':Path,'ROOT':root,'hashlib':hashlib})
disk_hash=source_build_id(root)
inputs=[]
for file in sorted(candidate,key=lambda p:p.relative_to(root).as_posix()):
    if not file.is_file() or file.is_symlink():continue
    try:file.resolve().relative_to(root)
    except ValueError:continue
    inputs.append({'path':file.relative_to(root).as_posix(),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
(out/'SOURCE_SNAPSHOT_INPUTS.json').write_text(json.dumps(inputs,indent=2),encoding='utf-8')
fingerprint=extract(attestation_tree,'_code_fingerprint',attestation_source,{'CodeType':CodeType,'hashlib':hashlib,'json':json})

module_files={'app.core.runtime_attestation':attestation_source,'app.core.runtime_identity':identity_source,
              'app.main':root/'app/main.py'}
compiled={}
def walk(code):
    yield code
    for value in code.co_consts:
        if isinstance(value,CodeType):yield from walk(value)
for module,file in module_files.items():
    # Compile only; no module body, imports, application initialization or handler execution.
    compiled[module]={c.co_qualname:c for c in walk(compile(file.read_text(encoding='utf-8-sig'),str(file),'exec',dont_inherit=True))}
scoped=[]
for entry in live['build']['loaded_code_manifest']:
    qualified=entry['symbol'].rsplit(':',1)[-1]
    item={**entry,'disk_comparison_status':'NOT_OBSERVABLE'}
    for module,codes in compiled.items():
        if qualified.startswith(module+'.'):
            name=qualified[len(module)+1:]
            code=codes.get(name)
            if code is not None:
                item['disk_code_sha256']=fingerprint(code)
                item['matches_disk_code']=item['disk_code_sha256']==entry['code_sha256']
                item['disk_comparison_status']='VERIFIED' if item['matches_disk_code'] else 'NOT_VERIFIED'
            break
    scoped.append(item)

process=live['process']
os_before=next((p for p in before['processes'] if p['ProcessId']==process['process_id']),None)
os_after=next((p for p in after['processes'] if p['ProcessId']==process['process_id']),None)
def normalized_time(value):return datetime.fromisoformat(value.replace('Z','+00:00'))
process_matches=bool(os_before and os_after and process['observed_process_id']==process['process_id']
    and process['valid_for_current_process'] is True
    and normalized_time(os_before['CreationTimeUtc'])==normalized_time(os_after['CreationTimeUtc'])
    ==normalized_time(process['process_start_time'])
    and os_before['ExecutablePath'].lower()==os_after['ExecutablePath'].lower()==process['executable_path'].lower())
receipt=live.get('provider_invocation')
result={'classification':'NEW_READONLY_OBSERVATION_AND_DISK_SOURCE_COMPARISON',
    'process_binding_status':'VERIFIED' if process_matches else 'NOT_VERIFIED',
    'repository_root':str(root),'process_working_directory':process['working_directory'],
    'working_directory_matches_repository':process['working_directory'].lower()==str(root).lower(),
    'runtime_instance':live['runtime_instance_id'],
    'readiness_instance_matches':live['runtime_instance_id']==live['correlation_readiness']['runtime_instance_id'],
    'process_source_snapshot':live['build']['source_build_hash'],'current_disk_source_snapshot':disk_hash,
    'process_source_matches_current_disk':live['build']['source_build_hash']==disk_hash,
    'source_snapshot_inputs':len(candidate),'source_algorithm_file_sha256':hashlib.sha256(identity_source.read_bytes()).hexdigest(),
    'source_algorithm_classification':'INSPECTED_CURRENT_DISK_FUNCTION_AST_NOT_APP_IMPORT',
    'live_scoped_loaded_code':live['build']['loaded_code_hash'],
    'live_scoped_current_registered_code':live['build']['current_registered_code_hash'],
    'live_scoped_binding':live['build']['loaded_code_binding'],
    'scoped_current_disk_comparison':scoped,
    'scope_limit':'Source compile comparison only, non-transitive; excludes dependency code, globals, closures, native/assets and actual provider.',
    'ACTIVE_PROCESS_BUILD':'NOT_DIRECTLY_VERIFIED','Runtime Identity':'NOT_VERIFIED',
    'provider_model_correlation':'NOT_VERIFIED','actual_model':receipt.get('actual_model') if receipt else None,
    'provider_invocation':receipt,'provider_receipt_exposed':live['correlation_readiness']['provider_receipt_exposed']}
(out/'IDENTITY_COMPARISON.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({key:value for key,value in result.items() if key not in {'scoped_current_disk_comparison'}},indent=2))
