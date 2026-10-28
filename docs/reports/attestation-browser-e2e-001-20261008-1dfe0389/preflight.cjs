const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {validate}=require('./validate_config.cjs');
const config=require('./playwright.mock.config.cjs');
const results=[];
results.push({id:'valid_config_before_launch',result:validate(config).status});
const cases={
  server:c=>c.webServer={command:'FORBIDDEN'},
  live_base_url:c=>c.use.baseURL='http://127.0.0.1:8000',
  wrong_test_selection:c=>c.testMatch='*.spec.ts',
  service_worker:c=>c.use.serviceWorkers='allow',
  missing_dns_boundary:c=>c.use.launchOptions.args=[],
  proxy_bypass:c=>c.use.launchOptions.proxy.bypass='*',
  wrong_executable:c=>c.use.launchOptions.executablePath='NOT_AN_EXECUTABLE',
  remote_connection:c=>c.use.connectOptions={wsEndpoint:'FORBIDDEN'},
  retry:c=>c.retries=1,
};
for(const [id,mutate] of Object.entries(cases)){
  const candidate=structuredClone(config);mutate(candidate);
  assert.throws(()=>validate(candidate));results.push({id,result:'REJECTED_AS_EXPECTED'});
}
for(const [id,change] of Object.entries({missing_mode:{CPLANE_ATTESTATION_E2E:undefined},live_flag:{CPLANE_E2E_LIVE:'1'},
  remote_environment:{PW_TEST_CONNECT_WS_ENDPOINT:'FORBIDDEN'}})){
  assert.throws(()=>validate(config,{...process.env,...change}));results.push({id,result:'REJECTED_AS_EXPECTED'});
}
const guard=globalThis.__NUSANTARA_MOCK_NETWORK_GUARD__;
try{globalThis.__NUSANTARA_MOCK_NETWORK_GUARD__=false;assert.throws(()=>validate(config));
  results.push({id:'missing_guard',result:'REJECTED_AS_EXPECTED'});
}finally{globalThis.__NUSANTARA_MOCK_NETWORK_GUARD__=guard;}
fs.writeFileSync(path.join(__dirname,'PREFLIGHT.json'),JSON.stringify({time:new Date().toISOString(),
  browser_launched:false,network_dispatched:false,results,final:validate(config)},null,2));
console.log('Prelaunch checks passed:',results.length,'; no browser/server/network launched.');
