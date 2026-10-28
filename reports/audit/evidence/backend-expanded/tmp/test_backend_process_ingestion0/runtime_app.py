from app.core.config import settings
settings.compose_configuration(project_root='C:\\Users\\dmaza\\mcp-starter\\reports\\audit\\evidence\\backend-expanded\\tmp\\test_backend_process_ingestion0',dotenv_environment={},environment={},overrides={'llm': {'model': 'fixture-local', 'base_url': 'http://127.0.0.1:58039'}, 'knowledge': {'root': 'C:\\Users\\dmaza\\mcp-starter\\reports\\audit\\evidence\\backend-expanded\\tmp\\test_backend_process_ingestion0\\knowledge', 'database': 'C:\\Users\\dmaza\\mcp-starter\\reports\\audit\\evidence\\backend-expanded\\tmp\\test_backend_process_ingestion0\\knowledge\\fixture.db'}})
from app.language.semantic.indobert_client import IndoBERTClient
IndoBERTClient.encode=lambda self,text:{'ok':True,'embedding':[1.0]+[0.0]*767}
from app.main import app
from app.api import routes
routes._language.semantic_intent_engine=None
import uvicorn
uvicorn.run(app,host='127.0.0.1',port=58040,log_level='warning',access_log=False)
