import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'e2e',testMatch:'operator-followup.spec.ts',workers:1,
 use:{baseURL:'http://127.0.0.1:5180',headless:true,viewport:{width:1440,height:1000}},
 outputDir:'../artifacts/ncp-v1-ui-followup-20261019/playwright',
 reporter:[['list'],['json',{outputFile:'../artifacts/ncp-v1-ui-followup-20261019/browser-results.json'}]]});
