const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const report=__dirname;
const plane=path.resolve(report,'../../../control-plane');
const executable=path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe');
const expectedSpec='27292c741acad5186cea4b856d172fcb090d387b004c77ee2385c7318e6f508d';
function validate(config,env=process.env){
  assert.equal(env.CPLANE_ATTESTATION_E2E,'MOCK_ONLY','MOCK_ONLY_MODE_REQUIRED');
  assert.equal(env.CPLANE_E2E_LIVE,undefined,'LIVE_FLAG_FORBIDDEN');
  assert.equal(globalThis.__NUSANTARA_MOCK_NETWORK_GUARD__,true,'NODE_GUARD_REQUIRED');
  for(const key of ['PW_TEST_CONNECT_WS_ENDPOINT','PLAYWRIGHT_CONNECT_WS_ENDPOINT','PW_TEST_CONNECT_HEADERS'])
    assert.equal(env[key],undefined,'REMOTE_BROWSER_FORBIDDEN');
  assert.equal(config.webServer,undefined,'SERVER_FORBIDDEN');
  assert.equal(config.projects,undefined,'ALTERNATE_PROJECT_FORBIDDEN');
  assert.equal(config.globalSetup,undefined,'GLOBAL_SETUP_FORBIDDEN');
  assert.equal(config.globalTeardown,undefined,'GLOBAL_TEARDOWN_FORBIDDEN');
  assert.equal(config.workers,1);assert.equal(config.retries,0);assert.equal(config.timeout,30000);
  assert.equal(config.testDir,path.join(plane,'e2e'));assert.equal(config.testMatch,'attestation.spec.ts');
  assert.equal(config.outputDir,path.join(report,'browser-results'));
  assert.equal(config.use.baseURL,'http://attestation-e2e.invalid','LIVE_BASE_URL_FORBIDDEN');
  assert.equal(config.use.headless,true);assert.equal(config.use.serviceWorkers,'block');
  assert.equal(config.use.browserName,'chromium');assert.equal(config.use.connectOptions,undefined);
  const launch=config.use.launchOptions;
  assert.equal(launch.executablePath,executable,'UNEXPECTED_BROWSER_EXECUTABLE');
  assert.equal(fs.statSync(executable).isFile(),true,'BROWSER_EXECUTABLE_REQUIRED');
  assert.deepEqual(launch.proxy,{server:'http://127.0.0.1:9',bypass:'<-loopback>'});
  assert.deepEqual(launch.args,['--disable-background-networking','--disable-component-update','--disable-sync',
    '--host-resolver-rules=MAP * ~NOTFOUND','--no-pings']);
  assert.equal(launch.ignoreDefaultArgs,undefined);
  assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path.join(plane,'e2e/attestation.spec.ts'))).digest('hex'),expectedSpec,
    'UNREVIEWED_SPEC_CHANGE');
  return {status:'READY_MOCK_ONLY',browser:executable,spec_sha256:expectedSpec,server:false,live:false};
}
module.exports={validate,plane,executable};
