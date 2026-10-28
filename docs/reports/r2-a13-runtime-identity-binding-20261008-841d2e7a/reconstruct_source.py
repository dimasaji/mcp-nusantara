"""Read-only virtual historical overlays; never restore files into the repository."""
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
out=Path(__file__).parent
inputs=json.loads((root/'docs/reports/r2-a12-readonly-discovery-20261008-c795a3e1/SOURCE_SNAPSHOT_INPUTS.json').read_text())
files=[entry['path'] for entry in inputs]
def calculate(overlays):
    digest=hashlib.sha256()
    for relative in sorted(files):
        path=root/relative
        assert path.suffix in {'.py','.json','.html','.css','.js','.toml'}
        assert not (path.suffix=='.json' and set(path.parts)&{'knowledge','rag','data','index','indices'})
        content=(root/overlays.get(relative,relative)).read_bytes()
        name=relative.encode()
        digest.update(len(name).to_bytes(8,'big'));digest.update(name)
        digest.update(len(content).to_bytes(8,'big'));digest.update(content)
    return 'sha256:'+digest.hexdigest()
phase_b={
    'app/api/runtime_verification.py':'docs/reports/r2-a11-phase-b-20261008-55fd917c/before/app__api__runtime_verification.py',
    'app/core/runtime_correlation.py':'docs/reports/r2-a11-phase-b-20261008-55fd917c/before/app__core__runtime_correlation.py',
}
older={**phase_b,'app/api/control_plane.py':'docs/reports/r2-a10-isolation-fix-20261008/before/control_plane.py'}
result={'classification':'VIRTUAL_SOURCE_HASH_RECONSTRUCTION_NOT_ACTIVE_MEMORY_PROOF','input_count':len(files),
    'current_disk':calculate({}),'pre_phase_b_virtual':calculate(phase_b),'pre_r2_a10_virtual':calculate(older),
    'overlays':older,'live_source_snapshot_from_r2_a12':'sha256:9789c2760ba7e78a4e6c5f6c7b1a5dec775c76f362cb40bb09d39e7d377a44df',
    'historical_c0_disk_snapshot':'sha256:fdc9a1e219ce55ab5957a58a31aef67a7a9a12277dabb03a1bad9b62871821ad'}
(out/'SOURCE_RECONSTRUCTION.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
