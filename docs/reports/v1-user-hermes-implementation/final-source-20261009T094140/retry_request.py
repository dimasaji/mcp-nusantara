"""Use the unchanged V1 request contract; preserve initial malformed probe evidence."""
from pathlib import Path
import sys

original = Path(__file__).resolve().parent.parent / 'verify_final_source_20261009T094140.py'
sys.path.insert(0, str(original.parent))
source = original.read_text(encoding='utf-8')
source = source.replace("{'message': 'Apa itu KTP-el?'", "{'user_input': 'Apa itu KTP-el?'")
source = source.replace("write('INVENTORY.json'", "write('INVENTORY.retry.json'")
source = source.replace("write('SELECTION.json'", "write('SELECTION.retry.json'")
source = source.replace("RUN/'request_failure_traceback.txt'", "RUN/'request_failure_traceback.retry.txt'")
source = source.replace("response['headers']['X-Request-ID']",
    "next(value for key,value in response['headers'].items() if key.lower() == 'x-request-id')")
sys.argv = [str(original), 'request']
exec(compile(source, str(original), 'exec'), {'__name__': '__main__', '__file__': str(original)})
