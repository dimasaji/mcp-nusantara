import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import {createHash} from 'node:crypto';
import {readFileSync, readdirSync} from 'node:fs';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
function sources(dir: string): string[] {return readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?sources(join(dir,e.name)):[join(dir,e.name)]).sort();}
function commit(){try{return execFileSync('C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe',['rev-parse','HEAD'],{cwd:'..',encoding:'utf8'}).trim();}catch{return 'NOT_VERIFIED';}}
const localServices = JSON.parse(readFileSync(new URL('../config/local-services.json', import.meta.url), 'utf8'));
const backendTarget = process.env.NUSANTARA_BACKEND_URL || `http://${localServices.host}:${localServices.backendPort}`;
export default defineConfig(({mode})=>({plugins:[react()], cacheDir:process.env.NUSANTARA_VITE_CACHE_DIR || 'node_modules/.vite', server:{host:localServices.host,port:localServices.frontendPort,strictPort:true,proxy:{'^/v1/chat(/history)?$':{target:backendTarget,changeOrigin:true},'^/v2/dev/inspection-preview$':{target:backendTarget,changeOrigin:true},'^/v1/knowledge/pipeline/(documents|status|watch|runs/[^/]+/retry)([?]|$)':{target:backendTarget,changeOrigin:true},'/v1/control-plane':{target:backendTarget,changeOrigin:true},'/health':{target:backendTarget,changeOrigin:true}}},preview:{host:localServices.host},
  define:{__CPLANE_BUILD__:JSON.stringify({version:'0.1.0',gitCommit:commit(),timestamp:new Date().toISOString(),environment:mode,sourceId:createHash('sha256').update(sources('src').map(f=>f+'\0'+readFileSync(f,'utf8')).join('\0')).digest('hex')})}}));

