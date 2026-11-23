import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';
import {fileURLToPath} from 'node:url';
// Offline component-test inputs, never current runtime or production evidence.
// Explicit environment overrides remain authoritative, including invalid paths.
const testInputs={
  CPLANE_SNAPSHOT_FILE:process.env.CPLANE_SNAPSHOT_FILE??fileURLToPath(new URL('./tests/fixtures/system-snapshot.json',import.meta.url)),
  R2_CPLANE_ISOLATED_EVIDENCE:process.env.R2_CPLANE_ISOLATED_EVIDENCE??fileURLToPath(new URL('./tests/fixtures/attestation-isolated.json',import.meta.url)),
};
export default defineConfig({root:fileURLToPath(new URL('.',import.meta.url)),cacheDir:process.env.NUSANTARA_VITEST_CACHE_DIR,resolve:{preserveSymlinks:!!process.env.NUSANTARA_TEST_RUN_DIR},plugins:[react()],test:{env:testInputs,cache:false,pool:'forks',environment:'jsdom',setupFiles:[fileURLToPath(new URL('./tests/setup.ts',import.meta.url))],include:['tests/**/*.test.ts','tests/**/*.test.tsx']},define:{__CPLANE_BUILD__:JSON.stringify({version:'test',gitCommit:'fixture',timestamp:'fixture',environment:'test',sourceId:'fixture'})}});
