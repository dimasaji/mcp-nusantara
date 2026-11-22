import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';

const source=readFileSync(join(process.cwd(),'vite.config.ts'),'utf8');

it('does not pin a Windows git executable',()=>{
 expect(source).not.toContain('C:/Users/dmaza');
});

it('uses the environment override with a system git fallback',()=>{
 expect(source).toContain("process.env.NUSANTARA_GIT_CMD || 'git'");
});
