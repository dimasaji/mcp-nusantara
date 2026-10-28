"""Temporary real app for browser verification; paid dispatch prohibited."""
import asyncio
import contextlib
import io
import json
import os
from pathlib import Path
import socket
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/control-plane-four-20261019'

async def verify():
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env',override=False)
    import httpx
    import uvicorn
    from app.models.openrouter import OpenRouterProvider,OpenRouterError
    calls=[]
    async def deny_paid(self,payload):
        calls.append('PROHIBITED_PAID_DISPATCH')
        raise OpenRouterError('DIAGNOSTIC_PAID_GENERATION_DISABLED')
    OpenRouterProvider.generate=deny_paid
    from app.main import app
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,lifespan='off',log_level='error',access_log=False))
    serving=asyncio.create_task(server.serve(sockets=[sock]))
    try:
        while not server.started:
            if serving.done():await serving
            await asyncio.sleep(.05)
        # Warm only retrieval, not inference, to test interaction separately from cold initialization.
        async with httpx.AsyncClient(timeout=120,trust_env=False) as client:
            await client.post(f'http://127.0.0.1:{port}/v1/knowledge/search',json={'query':'persyaratan permohonan data pribadi','top_k':3})
        temporary=OUT/'browser-tmp'
        temporary.mkdir(exist_ok=True)
        env=dict(os.environ,NUSANTARA_BACKEND_URL=f'http://127.0.0.1:{port}',NCP_OPERATOR_TOKEN=os.environ['NUSANTARA_ADMIN_TOKEN'],NUSANTARA_VITE_CACHE_DIR=str(OUT/'vite-cache'),TEMP=str(temporary),TMP=str(temporary))
        node=await asyncio.create_subprocess_exec('node',str(ROOT/'scripts/verify_control_plane_four.cjs'),cwd=ROOT,env=env,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        stdout,stderr=await node.communicate()
        (OUT/'browser-run.txt').write_bytes(stdout)
        return {'status':'PASS' if node.returncode==0 and not calls else 'FAIL','browser_exit':node.returncode,'paid_dispatch_attempts':len(calls),'production_restarted':False,'ingestion_watcher_started':False,'backend_port':port}
    finally:
        server.should_exit=True
        await serving
        sock.close()

with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
    try:result=asyncio.run(verify())
    except Exception as exc:result={'status':'FAIL','error_type':type(exc).__name__}
(OUT/'backend-browser.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
raise SystemExit(0 if result['status']=='PASS' else 1)
