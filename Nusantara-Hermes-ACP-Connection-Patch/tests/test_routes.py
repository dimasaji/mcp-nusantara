"""Exercise extracted uploaded boundary code without importing incomplete app."""
import ast
import hmac
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

BASE=Path(__file__).resolve().parents[1]

class HTTPError(Exception):
    def __init__(self,status_code,detail):
        self.status_code=status_code; self.detail=detail
        super().__init__(detail)

class BoundaryTests(unittest.TestCase):
    def setUp(self):
        source=(BASE/'payload/app/api/control_plane.py').read_text(encoding='utf-8')
        tree=ast.parse(source)
        names={'_human_acceptance_boundary','_hermes_connection_boundary'}
        selected=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
        self.env={'Request':object,'HTTPException':HTTPError,'urlsplit':urlsplit,'os':os}
        def admin(request):
            expected=os.environ.get('NUSANTARA_ADMIN_TOKEN','')
            supplied=request.headers.get('x-admin-token','')
            if not expected or not supplied or not hmac.compare_digest(expected,supplied):
                raise HTTPError(403,'admin token diperlukan')
        self.env['_admin_reviewer']=admin
        exec(compile(ast.Module(body=selected,type_ignores=[]),'<uploaded-boundaries>','exec'),self.env)
    def request(self,token='test-token',host='127.0.0.1',origin='http://127.0.0.1:5179',profile='NORMAL',method='POST',content_type='application/json'):
        return SimpleNamespace(client=SimpleNamespace(host=host),url=SimpleNamespace(hostname='127.0.0.1'),
            headers={'origin':origin,'content-type':content_type,'x-admin-token':token},method=method,
            app=SimpleNamespace(state=SimpleNamespace(runtime_profile=profile)))
    def call(self,**kwargs):
        with patch.dict(os.environ,{'NUSANTARA_ADMIN_TOKEN':'test-token','NUSANTARA_CONTROL_PLANE_READ_ONLY':'0'}):
            self.env['_hermes_connection_boundary'](self.request(**kwargs))
    def test_authorized_normal_loopback(self): self.call()
    def test_wrong_token_rejected(self):
        with self.assertRaises(HTTPError) as caught:self.call(token='wrong')
        self.assertEqual(caught.exception.status_code,403)
    def test_remote_rejected(self):
        with self.assertRaises(HTTPError):self.call(host='192.0.2.1')
    def test_foreign_origin_rejected(self):
        with self.assertRaises(HTTPError):self.call(origin='https://example.org')
    def test_non_json_post_rejected(self):
        with self.assertRaises(HTTPError):self.call(content_type='text/plain')
    def test_attestation_rejected(self):
        with self.assertRaises(HTTPError) as caught:self.call(profile='ATTESTATION')
        self.assertEqual(caught.exception.status_code,503)
    def test_evidence_readonly_rejected(self):
        with patch.dict(os.environ,{'NUSANTARA_ADMIN_TOKEN':'test-token','NUSANTARA_CONTROL_PLANE_READ_ONLY':'1'}):
            with self.assertRaises(HTTPError):self.env['_hermes_connection_boundary'](self.request())
    def test_get_allowed_without_content_type(self):self.call(method='GET',content_type='')

if __name__=='__main__':unittest.main()
