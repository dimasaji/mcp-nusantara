import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import {createHash} from 'node:crypto';
import {readFileSync, readdirSync} from 'node:fs';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
function sources(dir: string): string[] {return readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?sources(join(dir,e.name)):[join(dir,e.name)]).sort();}
const gitExecutable = () => process.env.NUSANTARA_GIT_CMD || 'git';
function commit(){try{return execFileSync(gitExecutable(),['rev-parse','HEAD'],{cwd:'..',encoding:'utf8'}).trim();}catch{return 'NOT_VERIFIED';}}
let localServices: {host?: string; backendPort?: number; frontendPort?: number} | null = null;
try {
  localServices = JSON.parse(readFileSync(new URL('../config/local-services.json', import.meta.url), 'utf8'));
} catch { /* local-services.json not available in production/CI builds */ }
const configuredHost = process.env.NUSANTARA_BACKEND_URL
  ? new URL(process.env.NUSANTARA_BACKEND_URL).host
  : (localServices?.host || '');
const configuredPort = process.env.NUSANTARA_BACKEND_URL
  ? new URL(process.env.NUSANTARA_BACKEND_URL).port || (new URL(process.env.NUSANTARA_BACKEND_URL).protocol === 'https:' ? '443' : '80')
  : (localServices?.backendPort?.toString() || '');
const backendTarget = process.env.NUSANTARA_BACKEND_URL || (configuredHost ? `http://${configuredHost}${configuredPort ? ':' + configuredPort : ''}` : '');
export default defineConfig(({mode})=>({plugins:[react()], cacheDir:process.env.NUSANTARA_VITE_CACHE_DIR || 'node_modules/.vite', server:{host:localServices?.host||'127.0.0.1',port:localServices?.frontendPort||5180,strictPort:true,proxy:{'^/v1/chat(/history)?$':{target:backendTarget,changeOrigin:true},'^/v1/runtime/readiness([?]|$)':{target:backendTarget,changeOrigin:true},'^/v1/dev/inspection-preview$':{target:backendTarget,changeOrigin:true},'^/v1/knowledge/pipeline/(documents|status|watch|runs/[^/]+/retry|reviews/[^/?]+(/source|/citation|/process|/decision|/metadata|/trials/[^/?]+/rating)?)([?]|$)':{target:backendTarget,changeOrigin:true},'/v1/control-plane':{target:backendTarget,changeOrigin:true},'/health':{target:backendTarget,changeOrigin:true}}},preview:{host:localServices?.host||'127.0.0.1'},
  define:{__CPLANE_BUILD__:JSON.stringify({version:'0.1.0',gitCommit:commit(),timestamp:new Date().toISOString(),environment:mode,sourceId:createHash('sha256').update(sources('src').map(f=>f+'\0'+readFileSync(f,'utf8')).join('\0')).digest('hex')})}}));


