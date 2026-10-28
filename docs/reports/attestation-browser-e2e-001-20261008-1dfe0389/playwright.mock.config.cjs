const path=require('node:path');
const {validate,plane,executable}=require('./validate_config.cjs');
const config={testDir:path.join(plane,'e2e'),testMatch:'attestation.spec.ts',workers:1,retries:0,timeout:30000,
  outputDir:path.join(__dirname,'browser-results'),
  reporter:[['list'],['json',{outputFile:path.join(__dirname,'RESULTS.json')}]],
  use:{baseURL:'http://attestation-e2e.invalid',headless:true,serviceWorkers:'block',browserName:'chromium',
    trace:'retain-on-failure',launchOptions:{executablePath:executable,
      proxy:{server:'http://127.0.0.1:9',bypass:'<-loopback>'},
      args:['--disable-background-networking','--disable-component-update','--disable-sync',
        '--host-resolver-rules=MAP * ~NOTFOUND','--no-pings']}}};
// Configuration evaluation happens before Playwright can launch browser/server.
validate(config);
module.exports=require(path.join(plane,'node_modules/@playwright/test')).defineConfig(config);
