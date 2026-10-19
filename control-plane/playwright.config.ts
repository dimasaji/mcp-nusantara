import {defineConfig} from '@playwright/test';
const live=process.env.CPLANE_E2E_LIVE==='1';
export default defineConfig({testDir:'e2e',use:{baseURL:'http://127.0.0.1:5179',headless:true},webServer:live?undefined:{command:'npm run dev -- --port 5174',url:'http://127.0.0.1:5174',reuseExistingServer:false},...(!live?{use:{baseURL:'http://127.0.0.1:5174',headless:true}}:{}),reporter:'list'});
