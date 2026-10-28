"""Run the explicitly requested local live browser test without logging secrets."""
import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

root = Path(__file__).resolve().parents[1]
token = dotenv_values(root / '.env').get('NUSANTARA_ADMIN_TOKEN')
assert token, 'Configured operator credential unavailable'
node = Path('C:/Users/dmaza/AppData/Local/hermes/node/node.exe')
temporary = root / 'artifacts/docling-ui/tmp'
temporary.mkdir(parents=True, exist_ok=True)
target = sys.argv[1] if len(sys.argv)>1 else 'e2e/docling-live.spec.ts'
result = subprocess.run([str(node), 'node_modules/playwright/cli.js', 'test', target, '--workers=1'],
    cwd=root / 'control-plane', env={**os.environ, 'CPLANE_E2E_LIVE': '1', 'NUSANTARA_DOCLING_LIVE': '1',
                                   'NUSANTARA_ADMIN_TOKEN': token, 'TEMP': str(temporary), 'TMP': str(temporary)}, shell=False)
raise SystemExit(result.returncode)
