"""Selected DevCore tests only; source strings are data, not executable scripts."""
import builtins
import importlib.abc
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
out = Path(__file__).parent
sys.path.insert(0,str(root))
os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
temporary = out/'temporary'
temporary.mkdir(exist_ok=True)
os.environ['TEMP']=os.environ['TMP']=str(temporary)
violations=[]
def prohibited(*args,**kwargs):
    violations.append('PROHIBITED_OPERATION')
    raise AssertionError('PROHIBITED_OPERATION')
sqlite3.connect=prohibited
os.system=prohibited
subprocess.Popen.__init__=prohibited
original_connect=socket.socket.connect
def socketpair_only(self,address):
    frame=sys._getframe(1)
    listener=frame.f_locals.get('lsock')
    if (frame.f_code is socket._fallback_socketpair.__code__ and listener is not None
            and address==listener.getsockname() and address[0] in ('127.0.0.1','::1')
            and address[1] not in (8000,5173,5174,11434,9)):
        return original_connect(self,address)
    return prohibited()
socket.socket.connect=socketpair_only
socket.socket.connect_ex=prohibited

def guarded(original):
    def opened(file,*args,**kwargs):
        name=str(file).lower().replace('\\','/')
        if name.endswith(('.db','.db-wal','.db-shm')) or '/data/knowledge/' in name:
            prohibited()
        return original(file,*args,**kwargs)
    return opened
builtins.open=guarded(builtins.open)
io.open=guarded(io.open)
class ForbiddenOwners(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith(('app.models','app.knowledge','app.language','app.api',
            'app.security.local_operator','app.approval.runtime_authorization')):
            prohibited()
sys.meta_path.insert(0,ForbiddenOwners())
import httpx
httpx.HTTPTransport.handle_request=prohibited
httpx.AsyncHTTPTransport.handle_async_request=prohibited
from app.approval import ApprovalQueue
for method in ('submit','consume','approve'):
    if hasattr(ApprovalQueue,method):
        setattr(ApprovalQueue,method,prohibited)
import pytest
mode=sys.argv[1]
if mode not in ('focused','regression'):
    raise SystemExit('INVALID_TEST_SELECTION')
paths=[str(root/'tests/v2/test_devcore_inspection.py')]
if mode=='regression':
    paths=[str(root/'tests/v2/test_devcore.py'), str(root/'tests/v2/test_devcore_grounding_response.py')]
class Evidence:
    def pytest_collection_modifyitems(self,items):
        (out/(mode+'_SELECTED_IDS.json')).write_text(json.dumps([i.nodeid for i in items],indent=2))
os.chdir(out)
result=pytest.main(paths+['-p','pytest_asyncio.plugin','-p','no:cacheprovider',
    '--basetemp',str(out/(mode+'-tmp')),'--junitxml',str(out/(mode+'_RESULTS.xml')),'-q'],plugins=[Evidence()])
(out/(mode+'_GUARDS.json')).write_text(json.dumps({'violations':violations,
    'pytest_exit':int(result),'real_model_owner_imports_blocked':True,'live_http_blocked':True,
    'approval_mutations_blocked':True,'sqlite_protected_io_blocked':True,
    'service_subprocess_blocked':True,'socket_allowance':'EXACT_STDLIB_SOCKETPAIR_ONLY'},indent=2))
raise SystemExit(result if not violations else 1)
