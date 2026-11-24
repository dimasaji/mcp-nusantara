import urllib.request,json,hashlib,re
result={}
for path in ['/health','/v1/health/ready','/']:
    with urllib.request.urlopen('http://127.0.0.1:8000'+path,timeout=10) as response:
        body=response.read();result[path]={'http_status':response.status,'sha256':hashlib.sha256(body).hexdigest()}
        if path=='/':
            result['frontend_assets']=[]
            for asset in re.findall(rb'(?:src|href)="(/assets/[^"]+)"',body):
                with urllib.request.urlopen('http://127.0.0.1:8000'+asset.decode()) as r:
                    data=r.read();result['frontend_assets'].append({'path':asset.decode(),'status':r.status,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
with urllib.request.urlopen('http://127.0.0.1:8000/openapi.json') as response:
    paths=json.load(response)['paths'];result['v1_chat_present']='/v1/chat' in paths;result['v2_routes_absent']=not any(p.startswith('/v2/') for p in paths)
print(json.dumps(result))
