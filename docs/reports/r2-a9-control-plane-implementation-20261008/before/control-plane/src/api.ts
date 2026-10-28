import {SystemHealthSchema,type SystemHealth} from './schemas';
export type SnapshotResult={state:SystemHealth;latencyMs:number;fetchedAt:string;source:string};
export async function fetchSnapshot(signal?:AbortSignal):Promise<SnapshotResult>{
  const start=performance.now();
  const response=await fetch('/v1/control-plane/snapshot',{method:'GET',credentials:'omit',cache:'no-store',signal});
  if(!response.ok)throw new Error(`Evidence API unavailable (${response.status}). No healthy state inferred.`);
  const state=SystemHealthSchema.parse(await response.json());
  return {state,latencyMs:Math.round(performance.now()-start),fetchedAt:new Date().toISOString(),source:'/v1/control-plane/snapshot'};
}
