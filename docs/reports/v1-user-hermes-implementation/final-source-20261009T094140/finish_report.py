"""Finalize append-only evidence, including all probe failures and actual retry command."""
from pathlib import Path
import sys

original = Path(__file__).resolve().parent.parent / 'verify_final_source_20261009T094140.py'
sys.path.insert(0, str(original.parent))
source = original.read_text(encoding='utf-8')
source = source.replace("'targeted_tests': read(RUN/'TARGETED_TEST.json'),", """'probe_failures': [
        {'stage': 'prepare', 'attribution': 'Evidence helper initially decoded pre-existing UTF-8 BOM as utf-8 instead of utf-8-sig; helper corrected before baseline capture; app source unchanged', 'evidence': 'PREPARE_INITIAL_FAILURE.txt'},
        {'stage': 'first HTTP probe', 'status': 422, 'attribution': 'Helper sent message instead of required user_input; rejected before model generation. Existing app contract preserved; retry uses user_input.', 'traceback': 'request_failure_traceback.txt'},
        {'stage': 'retry shell command', 'attribution': 'PowerShell quoting parser rejected inline Python before execution; standalone evidence-only retry helper used', 'evidence': 'RETRY_PARSER_FAILURE.txt'}],
        'actual_retry_command': '.venv/Scripts/python.exe -B docs/reports/v1-user-hermes-implementation/final-source-20261009T094140/retry_request.py',
        'candidate_stdout_stderr': ['CANDIDATE_STDOUT.txt', 'CANDIDATE_STDERR.txt'],
        'harness_file_sha256': __import__('hashlib').sha256(WRAPPER.read_bytes()).hexdigest(),
        'existing_files_checked': len(previous),
        'snapshot_errors': after['errors'],
        'targeted_tests': read(RUN/'TARGETED_TEST.json'),""")
sys.argv = [str(original), 'finish']
exec(compile(source, str(original), 'exec'), {'__name__': '__main__', '__file__': str(original)})
