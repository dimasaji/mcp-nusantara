"""No service observation; declared artifact fixtures are explicitly synthetic."""
import ast
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[3]
out = Path(__file__).parent
sys.path.insert(0, str(root))
from app.core.runtime_build_provenance import (BuildDefinition, BuildInput,
    BuildProvenanceOwner, ProcessBinding, assess_untrusted_build_provenance)

content = {'app.py': b'VALUE = 1\n', 'asset.txt': b'asset',
           'dependency.py': b'DEPENDENCY = 1\n', 'interpreter.bin': b'test-only-image'}
inventory = tuple(zip(content, ('APPLICATION_CODE', 'STATIC_ASSET', 'DEPENDENCY', 'INTERPRETER')))
definition = BuildDefinition(inventory, tuple(BuildInput(name, role,
    'sha256:'+hashlib.sha256(content[name]).hexdigest()) for name, role in inventory))
binding = ProcessBinding(1234, '2026-10-08T01:00:00+00:00', 'a'*32)
owner = BuildProvenanceOwner(definition, binding)
for name, value in content.items():
    owner.observe_consumed_artifact(name, value)
evidence = {'classification':'SYNTHETIC_DECLARED_ARTIFACTS_NOT_LIVE_APPLICATION',
    'definition':asdict(definition), 'process_binding':asdict(binding),
    'matching':owner.assess(definition,binding),
    'missing_expected':owner.assess(None,binding),
    'pid_reuse':owner.assess(definition,replace(binding,process_start='2026-10-08T02:00:00+00:00')),
    'untrusted':assess_untrusted_build_provenance({'complete':True,'trusted':True}),
    'repeat_equal':owner.assess(definition,binding)==owner.assess(definition,binding)}
(out/'SYNTHETIC_PROVENANCE.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')

# Reuse the exact existing source algorithm without importing app.main or identity.
tree = ast.parse((root/'app/core/runtime_identity.py').read_text(encoding='utf-8'))
node = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='source_build_id')
namespace = {'Path':Path,'ROOT':root,'hashlib':hashlib}
exec(compile(ast.Module(body=[node],type_ignores=[]),'source_build_id','exec'),namespace)
source_id = namespace['source_build_id'](root)
real = {'classification':'CURRENT_DISK_ONLY_NOT_LOADED_BUILD',
    'source_build_id':source_id, 'expected_build_id':None,
    'build_definition':'INCOMPLETE',
    'missing_definition':['independent closed runtime input inventory',
        'transitive Python/native dependency artifact inventory',
        'interpreter/stdlib artifact inventory', 'trusted execution-closure/load witness'],
    'observed_loaded_build_id':None,'process_identity':'NOT_OBSERVABLE_IN_THIS_PHASE',
    'runtime_instance_id':None,'active_process_build':'NOT_DIRECTLY_VERIFIED',
    'runtime_identity':'NOT_VERIFIED','provider_runtime_identity':'NOT_INVOKED',
    'authorization':'NOT_ACTIVATED','live_requests':0}
(out/'APPLICATION_BUILD_BOUNDARY.json').write_text(json.dumps(real,indent=2),encoding='utf-8')
print(json.dumps({'synthetic_declared_build_id':definition.build_id(),
    'synthetic_active_process_build':evidence['matching']['active_process_build'],
    'current_disk_source_build_id':source_id,'actual_expected_build_id':None,
    'actual_observed_loaded_build_id':None,'live_requests':0},indent=2))
