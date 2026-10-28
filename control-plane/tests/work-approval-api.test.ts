import {afterEach,expect,it,vi} from 'vitest';
import {fetchExecutionContext} from '../src/api';

afterEach(()=>vi.unstubAllGlobals());
function contract(){return {
 version:'nusantara.controlled-work.v1',scope:'CONTROLLED_FILE_WRITE',source:'Developer Core / change_plan.json',approval_validity_seconds:3600,approval_executes_work:false,
 steps:['PREPARE','VERIFY','DECIDE','AUTHORIZE','EXECUTE','AUDIT'].map(id=>({id,label:id,actor:'Sistem contoh',description:'Penjelasan contoh'})),
 decisions:['PASS','FAIL','HOLD'].map(code=>({code,label:code,description:'Keputusan contoh'})),
};}
it('reads the versioned workflow through the execution-context HTTP interface',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({workflow:contract()})}));
 const result=await fetchExecutionContext('fixture-token');
 expect(result.workflow?.approval_executes_work).toBe(false);
 expect(result.workflow?.steps.map(step=>step.id)).toEqual(['PREPARE','VERIFY','DECIDE','AUTHORIZE','EXECUTE','AUDIT']);
});
it.each(['order','duplicate','auto_execute','version'])('rejects an unsupported workflow: %s',async kind=>{
 const value=contract();
 if(kind==='order')value.steps.reverse();
 if(kind==='duplicate')value.decisions[1]={...value.decisions[0]};
 if(kind==='auto_execute')value.approval_executes_work=true;
 if(kind==='version')value.version='unknown';
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({workflow:value})}));
 await expect(fetchExecutionContext('fixture-token')).rejects.toThrow();
});
it('keeps older context responses readable without inventing a workflow',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({change_id:'legacy-plan'})}));
 expect((await fetchExecutionContext('fixture-token')).workflow).toBeUndefined();
});
