const fs=require('node:fs');
const path=require('node:path');
const file=path.resolve(__dirname,'../../../control-plane/src/engineering-console.tsx');
const before=fs.readFileSync(file,'utf8');
const needle="d.id==='ROLLBACK'?'docs/reports/v1-remaining-20261009T182840/EXECUTION_RESULTS.json':'docs/reports/weip-completion-20261009T104250Z/IMPLEMENTATION_REPORT.md'";
if(!before.includes(needle))throw new Error('EXPECTED_CONTEXT_MISSING');
fs.writeFileSync(file,before.replace(needle,"d.id==='FIXTURE'?evidence.fixtureApproval.reference:"+needle));
