import sys,json
for line in sys.stdin:
 print(json.dumps({'ok':True,'embedding':[1,2]}),flush=True)
