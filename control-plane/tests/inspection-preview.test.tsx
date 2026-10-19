import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import {afterEach,describe,it,expect,vi} from 'vitest';
import fs from 'node:fs';
import {readSnapshotFile} from './snapshot-file';
import ts from 'typescript';
import {fetchInspectionPreview} from '../src/api';
import {HumanContent,HumanProvider,InspectionPreviewPanel} from '../src/human';
import {SystemHealthSchema} from '../src/schemas';

const goal='Perbaiki RAG Nusantara.';
function evidence(input=goal){return {
  scope:'inspection-preview',profile:'NORMAL',source:'/v2/dev/inspection-preview',
  captured_at:'2026-10-08T12:00:00Z',runtime_identity:'NOT_VERIFIED',active_process_build:'NOT_VERIFIED',
  provider_model_correlation:'NOT_VERIFIED',inspection_preview:{
    goal:input,understanding:'Petakan retrieval sebelum menentukan perbaikan.',intent:'INSPECT',target:'RAG',
    status:'PREVIEW_READY',root_cause:'UNKNOWN',discovery:['Trace statis'],likely_files:['app/knowledge/rag.py'],
    plan:[{action:'STATIC_SOURCE_INSPECTION',step:'Trace source secara statis.'}],expected_evidence:['Source'],
    risk:'LOW',write_required:'NO',runtime_required:'NO',provider_required:'NO',database_required:'NO',
    human_decision:'NOT REQUIRED',next_step:'Tinjau preview.',requirements_scope:'PROPOSED_NEXT_STATIC_INSPECTION',
    goal_resolution_requirements:'UNKNOWN_PENDING_DISCOVERY',file_evidence:'CANDIDATES_NOT_INSPECTED',
    authorized_operations:[],boundaries:['NO WRITE','NO PROVIDER'],
  },
};}
afterEach(()=>{vi.unstubAllGlobals();vi.restoreAllMocks();});
describe('authenticated preview transport',()=>{
  it('sends one bounded request without redirects or token persistence',async()=>{
    const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>evidence()});vi.stubGlobal('fetch',fetch);
    const local=vi.spyOn(Storage.prototype,'setItem');
    await fetchInspectionPreview(goal,'fixture-only-token');
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledWith('/v2/dev/inspection-preview',expect.objectContaining({
      method:'POST',credentials:'omit',cache:'no-store',redirect:'error',
      headers:{'Content-Type':'application/json','X-Admin-Token':'fixture-only-token'},
      body:JSON.stringify({user_input:goal}),
    }));expect(local).not.toHaveBeenCalled();
  });
  it.each([403,422,503])('exposes HTTP %s without retry',async status=>{
    const fetch=vi.fn().mockResolvedValue({ok:false,status});vi.stubGlobal('fetch',fetch);
    await expect(fetchInspectionPreview(goal,'fixture')).rejects.toThrow(String(status));
    expect(fetch).toHaveBeenCalledTimes(1);
  });
  it('makes no request without token or bounded goal',async()=>{
    const fetch=vi.fn();vi.stubGlobal('fetch',fetch);
    await expect(fetchInspectionPreview(goal,'')).rejects.toThrow('Admin token');
    await expect(fetchInspectionPreview('x'.repeat(4001),'fixture')).rejects.toThrow('4000');
    await expect(fetchInspectionPreview('  ','fixture')).rejects.toThrow();expect(fetch).not.toHaveBeenCalled();
  });
  it('rejects wrong goal and unverifiable/authority-bearing responses',async()=>{
    for(const result of [evidence('Different goal'),{...evidence(),runtime_identity:'PASS'},
      {...evidence(),inspection_preview:{...evidence().inspection_preview,authorized_operations:['EXECUTE']}}]){
      vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>result}));
      await expect(fetchInspectionPreview(goal,'fixture')).rejects.toThrow();
    }
  });
  it('uses an exact preview-only proxy',()=>{
    const source=ts.createSourceFile('vite.config.ts',fs.readFileSync('vite.config.ts','utf8'),ts.ScriptTarget.Latest,true);
    const rules:string[]=[];
    function visit(node:ts.Node){
      if(ts.isPropertyAssignment(node)&&node.name.getText(source)==='proxy'&&ts.isObjectLiteralExpression(node.initializer)){
        for(const rule of node.initializer.properties){
          if(ts.isPropertyAssignment(rule)&&ts.isStringLiteral(rule.name))rules.push(rule.name.text);
        }
      }
      ts.forEachChild(node,visit);
    }
    visit(source);
    const matches=(url:string)=>rules.filter(rule=>rule.startsWith('^')?new RegExp(rule).test(url):url.startsWith(rule));
    expect(matches('/v2/dev/inspection-preview')).toHaveLength(1);
    for(const url of ['/v2/dev','/v2/chat','/v2/dev/inspection-preview/execute','/v2/dev/inspection-preview-extra']){
      expect(matches(url)).toHaveLength(0);
    }
  });
});
describe('separate inspection panel',()=>{
  it('requests only on explicit click, clears token and displays bounded evidence',async()=>{
    const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>evidence()});vi.stubGlobal('fetch',fetch);
    render(<InspectionPreviewPanel/>);expect(fetch).not.toHaveBeenCalled();
    expect(screen.getByRole('button',{name:'Preview inspection plan'})).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Admin token'),{target:{value:'fixture'}});
    fireEvent.click(screen.getByRole('button',{name:'Preview inspection plan'}));
    expect(screen.getByLabelText('Admin token')).toHaveValue('');
    await screen.findByRole('region',{name:'Preview evidence'});
    expect(screen.getByText(/candidates have not been inspected/)).toBeInTheDocument();
    expect(screen.getByText(/correlation: NOT VERIFIED/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Engineering goal'),{target:{value:'Buat Nusantara lebih cepat.'}});
    expect(screen.queryByRole('region',{name:'Preview evidence'})).not.toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(1);
  });
  it('displays refusal without successful preview or retained credentials',async()=>{
    const fetch=vi.fn().mockResolvedValue({ok:false,status:403});vi.stubGlobal('fetch',fetch);
    render(<InspectionPreviewPanel/>);fireEvent.change(screen.getByLabelText('Admin token'),{target:{value:'fixture'}});
    fireEvent.click(screen.getByRole('button',{name:'Preview inspection plan'}));
    expect(await screen.findByRole('alert')).toHaveTextContent('403');
    expect(screen.getByLabelText('Admin token')).toHaveValue('');
    expect(screen.queryByRole('region',{name:'Preview evidence'})).not.toBeInTheDocument();
  });
  it('cancels pending request when the panel closes',async()=>{
    const fetch=vi.fn().mockImplementation(()=>new Promise(()=>{}));vi.stubGlobal('fetch',fetch);
    const {unmount}=render(<InspectionPreviewPanel/>);
    fireEvent.change(screen.getByLabelText('Admin token'),{target:{value:'fixture'}});
    fireEvent.click(screen.getByRole('button',{name:'Preview inspection plan'}));
    const signal=fetch.mock.calls[0][1].signal as AbortSignal;unmount();expect(signal.aborted).toBe(true);
  });
  it('does not acknowledge System or alter engineering evidence after success',async()=>{
    const state=SystemHealthSchema.parse(readSnapshotFile());
    const before=JSON.stringify(state);vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>evidence()}));
    render(<HumanProvider><HumanContent stage="System" state={state} navigate={()=>{}} inspectRuntime={()=>{}}/></HumanProvider>);
    fireEvent.change(screen.getByLabelText('Admin token'),{target:{value:'fixture'}});
    fireEvent.click(screen.getByRole('button',{name:'Preview inspection plan'}));
    await waitFor(()=>expect(screen.getByRole('region',{name:'Preview evidence'})).toBeInTheDocument());
    expect(screen.getByLabelText('I have read the system summary and limitations.')).not.toBeChecked();
    expect(screen.getByRole('button',{name:/Continue to Evidence/})).toBeDisabled();
    expect(JSON.stringify(state)).toBe(before);
  });
});
