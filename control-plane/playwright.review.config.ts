import {resolve} from 'node:path';
import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'e2e',testMatch:'review-execution.spec.ts',workers:1,fullyParallel:false,
 timeout:45000,use:{baseURL:'http://127.0.0.1:5174',headless:true,channel:'msedge'},outputDir:resolve(import.meta.dirname,'../artifacts/v1-review-e2e/playwright-output'),reporter:[['list'],['json',{outputFile:resolve(import.meta.dirname,'../artifacts/v1-review-e2e/browser-results.json')}]],
 webServer:[
  {command:'..\\.venv\\Scripts\\python.exe ..\\tests\\serve_v1_review_fixture.py --port 9876',url:'http://127.0.0.1:9876/openapi.json',reuseExistingServer:false,timeout:60000},
  {command:'npm run dev -- --port 5174',url:'http://127.0.0.1:5174',reuseExistingServer:false,timeout:60000,env:{NUSANTARA_BACKEND_URL:'http://127.0.0.1:9876',NUSANTARA_VITE_CACHE_DIR:'../artifacts/v1-review-e2e/vite-cache'}}
 ]});
