import {defineConfig} from '@playwright/test';

export default defineConfig({
  testDir:'e2e',
  testMatch:'chat-settings.spec.ts',
  use:{baseURL:'http://127.0.0.1:5184',headless:true,
    launchOptions:{executablePath:process.env.CPLANE_BROWSER_EXECUTABLE||undefined}},
  webServer:{command:'npm run dev -- --port 5184',url:'http://127.0.0.1:5184',reuseExistingServer:false},
  reporter:'list',
});
