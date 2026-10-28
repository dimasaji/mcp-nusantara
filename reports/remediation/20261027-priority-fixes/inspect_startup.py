"""Record exception classes and frames, never configuration/credential values."""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
out=[]
for path in sorted((ROOT/'data/service-v1').glob('backend-*.err.log'),
                   key=lambda p:p.stat().st_mtime,reverse=True)[:3]:
    raw=path.read_bytes()
    encoding='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-16-le' if b'\x00' in raw[:200] else 'utf-8'
    text=raw.decode(encoding,errors='replace')[-70000:]
    out.append({'file':str(path.relative_to(ROOT)),
        'bytes':len(raw),'encoding':encoding,
        'launcher_missing_executable':'did not find executable' in text.lower(),
        'access_denied':'access is denied' in text.lower() or 'permission denied' in text.lower(),
        'frames':re.findall(r'File "([^"]+)", line (\d+), in ([^\r\n]+)',text)[-12:],
        'exception_types':re.findall(r'^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):',text,re.M)[-4:],
        'missing_modules_or_names':re.findall(r'''(?:No module named|name) ['"]([A-Za-z0-9_.]+)['"]''',text)[-4:]})
(Path(__file__).parent/'startup-diagnosis.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
