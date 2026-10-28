param(
    [Parameter(Mandatory=$true)][string]$Backup,
    [string]$Repository = 'C:\Users\dmaza\mcp-starter'
)
$ErrorActionPreference = 'Stop'
$python = Join-Path $Repository '.venv\Scripts\python.exe'
@'
import hashlib,json,pathlib,shutil,sys
root=pathlib.Path(sys.argv[1]).resolve(strict=True)
backup=pathlib.Path(sys.argv[2]).resolve(strict=True)
if not backup.is_relative_to(root/'.developer_backups'):
    raise RuntimeError('Backup harus berada dalam .developer_backups repository')
files=json.loads((backup/'restore-manifest.json').read_text(encoding='utf-8'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
for row in files:
    rel=pathlib.Path(row['path'])
    if rel.is_absolute() or '..' in rel.parts or not (root/rel).resolve().is_relative_to(root):
        raise RuntimeError('Path rollback tidak valid')
    if digest(root/rel)!=row['after_sha256']:
        raise RuntimeError('File berubah setelah patch: '+str(rel)+'; rollback otomatis dihentikan')
    if row['before_sha256'] is not None and digest(backup/rel)!=row['before_sha256']:
        raise RuntimeError('Backup tidak cocok: '+str(rel))
for row in reversed(files):
    target=root/row['path']
    if row['before_sha256'] is None: target.unlink()
    else: shutil.copy2(backup/row['path'],target)
print('ROLLBACK_SELESAI. Jalankan ulang build dan restart layanan sesuai prosedur repository.')
'@ | & $python - $Repository $Backup
if ($LASTEXITCODE -ne 0) { throw 'Rollback dihentikan; periksa output.' }
