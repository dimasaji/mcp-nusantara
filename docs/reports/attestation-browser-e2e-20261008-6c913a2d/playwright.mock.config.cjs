const path = require('node:path');
const {defineConfig} = require('../../../control-plane/node_modules/@playwright/test');
if(process.env.CPLANE_ATTESTATION_E2E !== 'MOCK_ONLY' || process.env.CPLANE_E2E_LIVE || !globalThis.__NUSANTARA_MOCK_NETWORK_GUARD__)
  throw new Error('UNSAFE_TEST_MODE');
module.exports = defineConfig({
  testDir:path.resolve(__dirname,'../../../control-plane/e2e'),
  testMatch:'attestation.spec.ts', workers:1, retries:0, timeout:30000,
  outputDir:path.join(__dirname,'browser-results-accepted'),
  reporter:[['list'],['json',{outputFile:path.join(__dirname,'RESULTS_ACCEPTED.json')}]],
  use:{baseURL:'http://attestation-e2e.invalid', headless:true, serviceWorkers:'block',
    browserName:'chromium', trace:'retain-on-failure',
    launchOptions:{executablePath:path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe'),
      proxy:{server:'http://127.0.0.1:9',bypass:'<-loopback>'},
      args:['--disable-background-networking','--disable-component-update','--disable-sync',
        '--host-resolver-rules=MAP * ~NOTFOUND','--no-pings']}},
});
