import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';
import {fileURLToPath} from 'node:url';
export default defineConfig({root:fileURLToPath(new URL('.',import.meta.url)),cacheDir:process.env.NUSANTARA_VITEST_CACHE_DIR,resolve:{preserveSymlinks:!!process.env.NUSANTARA_TEST_RUN_DIR},plugins:[react()],test:{cache:false,pool:'forks',environment:'jsdom',setupFiles:[fileURLToPath(new URL('./tests/setup.ts',import.meta.url))],include:['tests/**/*.test.ts','tests/**/*.test.tsx']},define:{__CPLANE_BUILD__:JSON.stringify({version:'test',gitCommit:'fixture',timestamp:'fixture',environment:'test',sourceId:'fixture'})}});
