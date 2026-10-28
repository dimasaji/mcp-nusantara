"""Real Chat/model browser canary; one paid dispatch, within existing approval."""
import asyncio
import contextlib
import io
import json
import os
from pathlib import Path
import socket
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/chat-p0-20261019'
sys.path.insert(0,str(ROOT))

async def verify():
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env',override=False)
    import httpx
    import uvicorn
    from app.models.openrouter import OpenRouterProvider,OpenRouterError
    from app.models.cost_ledger import CostLedger
    original=OpenRouterProvider.generate
    calls=[]
    no_paid=os.getenv('NCP_CHAT_CANARY_NO_PAID')=='1'
    async def bounded(self,payload):
        if no_paid or calls:
            raise OpenRouterError('DIAGNOSTIC_ONE_DISPATCH_LIMIT')
        current=CostLedger.read_existing_summary(ROOT/'data/openrouter_cost_v1.db')
        before=json.loads((OUT/'cost-before.json').read_text())
        old={r['request_id'] for r in before['history']}
        if len([r for r in current['history'] if r['request_id'] not in old])>=5:
            raise OpenRouterError('APPROVED_TOTAL_DISPATCH_LIMIT')
        calls.append('real-openrouter-call')
        return await original(self,payload)
    OpenRouterProvider.generate=bounded
    from app.main import app
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,lifespan='off',log_level='error',access_log=False))
    serving=asyncio.create_task(server.serve(sockets=[sock]))
    try:
        while not server.started:
            if serving.done():await serving
            await asyncio.sleep(.05)
        async with httpx.AsyncClient(timeout=120,trust_env=False) as client:
            await client.post(f'http://127.0.0.1:{port}/v1/knowledge/search',json={'query':'persyaratan permohonan data pribadi','top_k':3})
        temporary=OUT/'browser-tmp';temporary.mkdir(exist_ok=True)
        env=dict(os.environ,NCP_CHAT_BUDGET_APPROVED='USD0.05_MAX5',NCP_CHAT_PHASE='sop-no-dispatch' if no_paid else 'canary-after-fix',
            NCP_CHAT_EVIDENCE_TAG='sop-after-fix' if no_paid else 'canary-after-fix',NCP_CHAT_TEMP_BACKEND=f'http://127.0.0.1:{port}',NCP_CHAT_NO_PAID_SERVER_GUARD='1' if no_paid else '0',
            NCP_OPERATOR_TOKEN=os.environ['NUSANTARA_ADMIN_TOKEN'],TEMP=str(temporary),TMP=str(temporary),
            NUSANTARA_VITE_CACHE_DIR=str(OUT/'vite-cache'))
        child=await asyncio.create_subprocess_exec('node',str(ROOT/'scripts/verify_chat_p0.cjs'),cwd=ROOT,env=env,
            stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        stdout,stderr=await child.communicate()
        (OUT/'canary-run.txt').write_bytes(stdout)
        return {'status':'PASS' if child.returncode==0 else 'FAIL','browser_exit':child.returncode,
            'real_provider_calls':len(calls),'production_restarted':False,'backend_port':port}
    finally:
        server.should_exit=True
        await serving
        sock.close()

with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
    try:result=asyncio.run(verify())
    except Exception as exc:result={'status':'FAIL','error_type':type(exc).__name__}
(OUT/('sop-result.json' if os.getenv('NCP_CHAT_CANARY_NO_PAID')=='1' else 'canary-result.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
raise SystemExit(0 if result['status']=='PASS' else 1)
