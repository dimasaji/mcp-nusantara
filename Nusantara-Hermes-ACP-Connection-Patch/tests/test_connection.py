import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bridge',BASE/'payload/app/developer_core/hermes_acp_connection.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)

class ACPTests(unittest.TestCase):
    def exchange(self, code, timeout=2):
        with tempfile.TemporaryDirectory() as folder:
            script=Path(folder)/'server.py';script.write_text(code,encoding='utf-8')
            return bridge._exchange([sys.executable,str(script)],folder,timeout=timeout)

    def valid_server(self, result=None):
        result=result or {'protocolVersion':1,'agentInfo':{'name':'hermes-agent','version':'0.21.5'},'authMethods':[{'id':'openrouter'}]}
        # Require exactly initialize, no session/new or prompt, and keep stdin open.
        return ('import sys,json\n'
                'r=json.loads(sys.stdin.readline())\n'
                'assert r["method"]=="initialize"\n'
                'assert r["params"]["clientCapabilities"]=={}\n'
                'assert not sys.stdin.closed\n'
                'print(json.dumps({"jsonrpc":"2.0","id":1,"result":'+repr(result)+'}),flush=True)\n'
                'assert sys.stdin.read()==""\n')

    def test_initialize_without_prompt(self):
        result=self.exchange(self.valid_server())
        self.assertEqual(result['agent_version'],'0.21.5')
        self.assertTrue(result['openrouter_auth_advertised'])
        self.assertEqual(len(result['response_sha256']),64)

    def test_closed_before_reply(self):
        with self.assertRaisesRegex(ValueError,'ACP_'):
            self.exchange('pass')

    def test_wrong_protocol_rejected(self):
        with self.assertRaisesRegex(ValueError,'PROTOCOL'):
            self.exchange(self.valid_server({'protocolVersion':2,'agentInfo':{'name':'hermes-agent','version':'1'}}))

    def test_wrong_agent_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNEXPECTED_AGENT'):
            self.exchange(self.valid_server({'protocolVersion':1,'agentInfo':{'name':'other','version':'1'}}))

    def test_json_error_rejected(self):
        with self.assertRaisesRegex(ValueError,'REJECTED'):
            self.exchange('import sys,json\nsys.stdin.readline()\nprint(json.dumps({"jsonrpc":"2.0","id":1,"error":{"message":"secret"}}),flush=True)\nsys.stdin.read()')

    def test_non_protocol_output(self):
        with self.assertRaisesRegex(ValueError,'INVALID_JSON'):
            self.exchange('print("secret startup text",flush=True)')

    def test_output_bounded(self):
        with self.assertRaisesRegex(ValueError,'OUTPUT_LIMIT'):
            self.exchange('print("x"*70000,flush=True)')

    def test_timeout_and_process_cleanup(self):
        with self.assertRaisesRegex(ValueError,'TIMEOUT'):
            self.exchange('import time\ntime.sleep(10)',timeout=0.1)

    def test_client_requests_not_executed(self):
        prefix=('import sys,json\nr=json.loads(sys.stdin.readline())\n'
          'print(json.dumps({"jsonrpc":"2.0","id":8,"method":"fs/read_text_file","params":{}}),flush=True)\n'
          'reply=json.loads(sys.stdin.readline())\nassert reply["error"]["code"]==-32601\n')
        result={'protocolVersion':1,'agentInfo':{'name':'hermes-agent','version':'0.21.5'}}
        code=prefix+'print(json.dumps({"jsonrpc":"2.0","id":1,"result":'+repr(result)+'}),flush=True)\nsys.stdin.read()'
        self.assertEqual(self.exchange(code)['agent_name'],'hermes-agent')

    def test_get_state_does_not_spawn(self):
        bridge._last=None
        with patch.object(bridge.subprocess,'Popen',side_effect=AssertionError('spawn')):
            self.assertEqual(bridge.state()['status'],'NOT_CHECKED')

    def test_probe_sanitizes_error(self):
        with patch.object(bridge,'_command',side_effect=PermissionError('secret-key')):
            result=bridge.probe()
        self.assertEqual(result['status'],'UNAVAILABLE')
        self.assertNotIn('secret-key',json.dumps(result))
        self.assertFalse(result['task_execution_enabled'])

    def test_probe_records_timestamp(self):
        with patch.object(bridge,'_command',return_value=(BASE,[])), patch.object(bridge,'_exchange',return_value={'agent_version':'0.21.5'}):
            result=bridge.probe()
        self.assertEqual(result['status'],'CONNECTED')
        self.assertIsNotNone(result['checked_at'])
        self.assertFalse(result['cost_ledger_integrated'])

    def test_busy_no_duplicate_process(self):
        bridge._lock.acquire()
        try:
            with patch.object(bridge,'_command',side_effect=AssertionError('spawn')):
                self.assertEqual(bridge.probe()['status'],'BUSY')
        finally:
            bridge._lock.release()

if __name__=='__main__': unittest.main()
