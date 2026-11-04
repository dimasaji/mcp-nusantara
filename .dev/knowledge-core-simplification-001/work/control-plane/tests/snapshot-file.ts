import {readFileSync,statSync} from 'node:fs';
import {resolve} from 'node:path';

// Explicit test input only. Never acquire live evidence or invent a fallback.
export function readSnapshotFile(variable='CPLANE_SNAPSHOT_FILE'):unknown {
  const supplied=process.env[variable]?.trim();
  const missing=(reason:string)=>new Error(`[CONTROL_PLANE_TEST_PREREQUISITE] ${variable}: ${reason}. Set an explicit readable JSON evidence file. Local fixtures are test data, not production verification.`);
  if(!supplied)throw missing('path is not configured');
  const path=resolve(supplied);
  try{
    if(!statSync(path).isFile())throw new Error('not a regular file');
  }catch{throw missing(`file unavailable: ${path}`);}
  let text:string;
  try{text=readFileSync(path,'utf8');}catch{throw missing(`file unreadable: ${path}`);}
  try{return JSON.parse(text.replace(/^\uFEFF/,''));}
  catch{throw missing(`invalid JSON: ${path}`);}
}
