import {defineConfig} from '../../../control-plane/node_modules/@playwright/test/index.mjs';
import {fileURLToPath} from 'node:url';
const repo=fileURLToPath(new URL('../../../',import.meta.url));
const node='C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';
export default defineConfig({
  testDir:repo+'control-plane/e2e',testMatch:'chat-settings.spec.ts',
  workers:1,retries:0,timeout:45000,
  outputDir:fileURLToPath(new URL('./browser-output/',import.meta.url)),
  reporter:[['json',{outputFile:fileURLToPath(new URL('./browser-results.json',import.meta.url))}]],
  use:{baseURL:'http://127.0.0.1:5197',headless:true,serviceWorkers:'block',trace:'off',video:'off'},
  webServer:{command:`"${node}" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5197`,
    cwd:repo+'control-plane',url:'http://127.0.0.1:5197',reuseExistingServer:false,
    env:{NUSANTARA_VITE_CACHE_DIR:fileURLToPath(new URL('./vite-cache/',import.meta.url))}},
});
