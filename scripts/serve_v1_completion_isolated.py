"""Actual V1 application on isolated data; no operational uploads or paid calls."""
from pathlib import Path
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
RUN=ROOT/'artifacts/nusantara-e2e-20261016-1018/isolated-runtime'
RUN.mkdir(parents=True,exist_ok=True)
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ['NUSANTARA_LAYA_ENABLED']='false'
os.environ['NUSANTARA_DATA_DIR']=str(RUN/'data')
os.environ['NUSANTARA_KNOWLEDGE_DB']=str(RUN/'knowledge/chat.db')
os.environ['LLM_PROVIDER']='ollama'
os.environ['LLM_BASE_URL']='http://127.0.0.1:11434'
os.environ['PORT']='8766'
os.environ.pop('NUSANTARA_RUNTIME_PORT',None)
from dotenv import dotenv_values
if not os.environ.get('NUSANTARA_ADMIN_TOKEN'):
    value=dotenv_values(ROOT/'.env',interpolate=False).get('NUSANTARA_ADMIN_TOKEN')
    if value:os.environ['NUSANTARA_ADMIN_TOKEN']=value
from app.core.config import settings
settings.compose_configuration(overrides={'knowledge':{'root':str(RUN/'knowledge'),
    'database':str(RUN/'knowledge/chat.db')}})
from app.main import app
if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=8766,log_level='warning')
