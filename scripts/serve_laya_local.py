"""Run the installed Laya HTTP server once, offline, in .venv-laya.

Usage: .venv-laya/Scripts/python.exe scripts/serve_laya_local.py
Configuration is persistent; no shell activation or transient HF_HOME required.
"""
import json
import os
from pathlib import Path
import socket
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / 'config/laya-local.json').read_text(encoding='utf-8'))
    if config['host'] != '127.0.0.1':
        raise SystemExit('LAYA_LOOPBACK_REQUIRED')
    if Path(sys.prefix).resolve() != (root / '.venv-laya').resolve():
        raise SystemExit('USE_ISOLATED_VENV_LAYA')
    checkpoint = (root / config['checkpoint']).resolve(strict=True)
    for name in ('rl_agent_config.json', 'model.safetensors', 'encoder/config.json', 'tokenizer/tokenizer.json'):
        if not (checkpoint / name).is_file():
            raise SystemExit('LAYA_LOCAL_CHECKPOINT_INCOMPLETE')
    with socket.socket() as probe:
        try:
            probe.bind((config['host'], config['port']))
        except OSError:
            raise SystemExit('LAYA_PORT_IN_USE') from None
    os.environ.update({
        'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
        'LAYA_HOST': config['host'], 'LAYA_PORT': str(config['port']),
        'LAYA_DEVICE': 'cpu', 'LAYA_THREADS': str(config['threads']),
        'LAYA_PRELOAD': '1', 'LAYA_MODELS': 'multilingual',
        'LAYA_DEFAULT_MODEL': 'multilingual', 'LAYA_MAX_LOADED': '1',
        'LAYA_IDLE_UNLOAD_SECONDS': '0', 'LAYA_AUTO_TASK': '0',
        'LAYA_MAX_CONCURRENT': '2', 'LAYA_MAX_TOKEN_BUDGET': '1024',
        'LAYA_EXTRA_MODELS': json.dumps({'multilingual': str(checkpoint)}),
    })
    from importlib.metadata import version
    if version('laya') != '0.4.8':
        raise SystemExit('LAYA_VERSION_REQUIRES_REVALIDATION')
    from laya.serve import main as serve
    serve()


if __name__ == '__main__':
    main()
