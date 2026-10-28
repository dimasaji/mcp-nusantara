import hashlib
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))
before=read('BEFORE.json');after=read('AFTER.json');audit=read('CHANGE_AUDIT.json')
execution=read('TEST_EXECUTION_02.json');tests=read('TEST_RESULTS.json')
p1=read('PROCESS_BEFORE.json');p2=read('PROCESS_AFTER.json')
previous=ROOT/'docs/reports/ui04-chat-timeout-20261009-130937/CHANGE_AUDIT_UTF8.json'
prior=json.loads(previous.read_text(encoding='utf-8'))
report={
 'timestamp':datetime.now(timezone(timedelta(hours=7))).isoformat(),'status':'VERIFIED_SCOPED','v1_acceptance':'HOLD','v2':'DEFERRED',
 'requested_commands':{'before':before['git_commands'],'npm_test':execution,'after':after['git_commands']},
 'test_result':{'exit_code':execution['exit_code'],'total':tests['numTotalTests'],'pass':tests['numPassedTests'],'fail':tests['numFailedTests'],'pending':tests['numPendingTests'],'success':tests['success'],'new_run':True,'output_evidence':['TEST_EXECUTION_02.json','TEST_RESULTS.json']},
 'scope_analysis':{'working_tree_contains_preexisting_other_changes':True,'two_file_git_diff_empty_reason':'control-plane is untracked; ordinary git diff does not include these files. Empty output is not proof that UI04 has no changes.','ui04_task_diff':str(ROOT/'docs/reports/ui04-chat-timeout-20261009-130937/UI04_EXACT_LF.diff'),'prior_ui04_changed_files':prior['changes']['modified'],'current_hashes_match_verified_ui04':before['hashes']==prior['after_hashes'],'changes_during_this_test_run':audit['changes_during_verification'],'hashes_before':before['hashes'],'hashes_after':after['hashes'],'git_status_stdout_unchanged':before['git_commands'][0]['stdout']==after['git_commands'][0]['stdout']},
 'errors_and_warnings':[
  {'stage':'initial npm launch','exit_code':1,'error':'MODULE_NOT_FOUND: NODE_OPTIONS path backslashes were interpreted as escapes; corrected to forward slashes in evidence runner only. No tests executed in first attempt.','evidence':'TEST_EXECUTION.json'},
  {'stage':'Python console printing after successful npm run','exit_code':1,'error':'UnicodeEncodeError printing checkmark under Windows cp1252. npm already exit0 and all stdout/stderr/JSON saved before print. Read saved evidence, no test rerun needed.','npm_exit_code':0},
  {'stage':'Git status before/after','exit_code':0,'warning':'Permission denied on five pre-existing temp directories; complete stderr retained in BEFORE/AFTER.json'},
  {'stage':'Git diff --check before/after','exit_code':0,'warning':'Existing LF→CRLF warnings; no whitespace errors; full stderr retained'},
  {'stage':'npm stderr','exit_code':0,'notice':'npm update notice only; no package installation or update performed'}
 ],
 'safeguards':{'package_script':'test: vitest run','invocation':'Existing installed Node/npm CLI runs npm --prefix control-plane test -- --run tests/assistant.test.tsx; added configLoader runner/no-cache/single-thread/report options to prevent tooling writes and preserve output.','network_db_process':'Existing test guard active in test child: no network server/listen/connect, DB or production-data access; only esbuild transform allowed','writes':'Test file writes confined to fresh evidence; report-local npm cache used transiently. No source/config/dependency changes.','runtime_pid33160_unchanged':p1['process']==p2['process'] and p1['listeners']==p2['listeners'],'server_started':False,'port8000_changed':False,'backend_db_commit_changes':False},
 'limitations':['Git diff --check covers tracked files; target files untracked, so two-file scope established by captured UI04 diff and unchanged SHA256 instead.','Five inaccessible historical test directories excluded from complete inventory; no clearing/permission changes attempted.','Mocked UI tests do not establish native runtime/provider/production acceptance.'],
 'evidence':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.glob('*.json'))],
 'stop':'Requested verification complete. No activation or production acceptance.'}
with (OUT/'REVERIFICATION_REPORT.json').open('x',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=False,indent=2)
print(json.dumps({'report':str(OUT/'REVERIFICATION_REPORT.json'),'npm_exit':execution['exit_code'],'pass':tests['numPassedTests'],'fail':tests['numFailedTests'],'file_changes':audit['changes_during_verification']}))
