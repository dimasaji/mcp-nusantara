"""Attribute changes against captured hashes, including inherited untracked code."""
import difflib
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
out = Path(__file__).parent
baseline = json.loads((out/'FILES_BEFORE.json').read_text(encoding='utf-8-sig'))
baseline_hashes = {entry['path']:entry['sha256'] for entry in baseline}
identity_before = (out/'runtime_identity.py.before').read_text(encoding='utf-8')
identity_after = (root/'app/core/runtime_identity.py').read_text(encoding='utf-8')
attestation_after = (root/'app/core/runtime_attestation.py').read_text(encoding='utf-8')
# Reconstruct the inherited untracked file solely by removing this task's exact
# patch. Accept the reconstruction only if it reproduces the pre-edit byte hash.
attestation_before = attestation_after.replace(
    'from app.core import runtime_build_provenance as build_provenance\n','')
added = '''                     install_runtime_attestation, build_provenance._hash, build_provenance._name,
                     build_provenance._result, build_provenance.BuildDefinition.validate,
                     build_provenance.BuildDefinition.build_id, build_provenance.ProcessBinding.valid,
                     build_provenance.BuildProvenanceOwner.__init__,
                     build_provenance.BuildProvenanceOwner.observe_consumed_artifact,
                     build_provenance.BuildProvenanceOwner.assess,
                     build_provenance.assess_untrusted_build_provenance):'''
attestation_before = attestation_before.replace(added, '                     install_runtime_attestation):')
assert hashlib.sha256(attestation_before.encode()).hexdigest() == baseline_hashes['app/core/runtime_attestation.py']
(out/'runtime_attestation.py.before.reconstructed').write_text(attestation_before,encoding='utf-8')
changes = [('app/core/runtime_identity.py',identity_before,identity_after),
           ('app/core/runtime_attestation.py',attestation_before,attestation_after)]
for name in ('app/core/runtime_build_provenance.py','tests/test_runtime_build_provenance.py'):
    changes.append((name,'',(root/name).read_text(encoding='utf-8')))
diff = ''.join(''.join(difflib.unified_diff(before.splitlines(keepends=True),
    after.splitlines(keepends=True),fromfile='before/'+name,tofile='after/'+name))
    for name,before,after in changes)
(out/'IMPLEMENTATION.diff').write_text(diff,encoding='utf-8')
(out/'CHANGED_FILES.json').write_text(json.dumps({
    'existing_application_modified':['app/core/runtime_identity.py','app/core/runtime_attestation.py'],
    'application_created':['app/core/runtime_build_provenance.py'],
    'test_created':['tests/test_runtime_build_provenance.py'],
    'attestation_before_reconstruction_hash_verified':True,
    'control_plane_modified':False,'public_response_schema_modified':False,
    'runtime_verification_or_correlation_modified':False},indent=2),encoding='utf-8')
print(json.dumps({'diff_lines':len(diff.splitlines()),'files':len(changes),
                  'reconstruction_hash_verified':True}))
