import json,sys
for line in sys.stdin:
 value=json.loads(line)
 print(json.dumps({'ok':True,'text':value['text']},ensure_ascii=True),flush=True)
