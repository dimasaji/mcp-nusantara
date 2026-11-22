import {render,screen,fireEvent,within} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {existsSync,readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {EngineeringConsole} from '../src/engineering-console';
import {Page} from '../src/ui';
import evidence from '../src/engineering-evidence';

afterEach(()=>vi.unstubAllGlobals());
function show(name:string){fireEvent.click(screen.getByRole('button',{name}));}
describe('read-only engineering console',()=>{
  it('uses the existing engineering overview without querying the application',()=>{
    const fetch=vi.fn(()=>{throw new Error('Network forbidden')});vi.stubGlobal('fetch',fetch);
    render(<Page name="Overview"/>);
    expect(screen.getByRole('heading',{name:'Engineering Console'})).toBeInTheDocument();
    expect(screen.getAllByText(/FAIL \/ HOLD/).length).toBeGreaterThan(0);
    expect(screen.getByText(/snapshot bukti historis/)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });
  it('renders all 22 phases without borrowing acceptance from WEIP',()=>{
    render(<EngineeringConsole/>);show('Tahapan 0–21');
    const panel=screen.getByRole('region',{name:'Tahapan 0–21'});
    expect(within(panel).getAllByRole('article')).toHaveLength(22);
    expect(within(panel).getAllByText('NOT_VERIFIED')).toHaveLength(22);
    expect(within(panel).queryByText('PASS')).not.toBeInTheDocument();
    expect(within(panel).getByRole('heading',{name:'Fase 21'})).toBeInTheDocument();
  });
  it('renders twelve gates and preserves the authorization boundary',()=>{
    render(<EngineeringConsole/>);show('WEIP-01–12');
    const panel=screen.getByRole('region',{name:'WEIP-01–12'});
    expect(within(panel).getAllByRole('article')).toHaveLength(12);
    expect(within(panel).getAllByText('REVIEW_REQUIRED')).toHaveLength(2);
    expect(within(panel).getByText('NOT_AUTHORIZED')).toBeInTheDocument();
    expect(within(panel).getByText('DEFERRED')).toBeInTheDocument();
  });
  it('preserves initial failure and counts exclusions separately from skip',()=>{
    render(<EngineeringConsole/>);show('Tes & Bukti');
    const rows=screen.getAllByRole('row');
    const failed=rows.find(r=>r.textContent?.includes('targeted-20261009-174413'))!;
    expect(within(failed).getByText('FAIL')).toBeInTheDocument();
    const regression=rows.find(r=>r.textContent?.includes('regression-20261009-174852'))!;
    expect(within(regression).getByText('154')).toBeInTheDocument();
    expect(within(regression).getByText('6')).toBeInTheDocument();
    expect(screen.getByText(/Tidak dihitung sebagai PASS atau SKIP/)).toBeInTheDocument();
  });
  it('does not invent a preservation cause or loaded runtime identity',()=>{
    render(<EngineeringConsole/>);
    expect(screen.getByText(/Penyebab dan pelaku tidak terbukti/)).toBeInTheDocument();
    expect(screen.getByText(/Database aktif tidak diperiksa/)).toBeInTheDocument();
    expect(screen.getByText(evidence.diskFingerprint)).toBeInTheDocument();
    expect(evidence.preservation.attribution).toBe('NOT_VERIFIED');
    expect(evidence.runtimeIdentity).toBe('NOT_VERIFIED');
  });
  it('offers navigation only, with no persistence or runtime requests',()=>{
    const fetch=vi.fn(()=>{throw new Error('Network forbidden')});vi.stubGlobal('fetch',fetch);
    render(<EngineeringConsole/>);
    for(const name of ['Tahapan 0–21','WEIP-01–12','Tes & Bukti','Keputusan manusia','Ringkasan'])show(name);
    show('Keputusan manusia');
    expect(screen.getByRole('heading',{name:'Transaksi adapter dan rollback'})).toBeInTheDocument();
    expect(screen.getAllByRole('button')).toHaveLength(5);
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });
  it('binds available evidence to archive checksums and keeps removed archives historical',()=>{
    for(const s of evidence.sources){
      const path=resolve('..',s.path);
      expect(s.sha256).toMatch(/^[a-f0-9]{64}$/);
      if(!existsSync(path))continue;
      const bytes=readFileSync(path);
      expect(createHash('sha256').update(bytes).digest('hex')).toBe(s.sha256);
    }
    for(const t of evidence.tests){
      const path=resolve('..',t.reference);
      if(!existsSync(path))continue;
      const xml=readFileSync(path,'utf8');
      for(const attr of ['tests','failures','errors','skipped'] as const){
        expect(xml).toContain(`${attr}="${t[attr]}"`);
      }
    }
    expect(evidence.mode).toBe('HISTORICAL_ARTIFACT_SNAPSHOT');
    expect(evidence.runtimeIdentity).toBe('NOT_VERIFIED');
  });
  it('shows the newer offline results without claiming runtime verification',()=>{
    render(<EngineeringConsole/>);
    expect(screen.getByRole('heading',{name:'OpenRouter dan workflow LangGraph'})).toBeInTheDocument();
    expect(screen.getByText(/Provider mock; Ollama tetap default/)).toBeInTheDocument();
    expect(evidence.runtimeIdentity).toBe('NOT_VERIFIED');
    expect(evidence.activeIntegration).toBe('NOT_AUTHORIZED');
    show('Tes & Bukti');
    const rows=screen.getAllByRole('row');
    const rag=rows.find(r=>r.textContent?.includes('regression-20261009-183418'))!;
    expect(within(rag).getByText('208')).toBeInTheDocument();
    expect(within(rag).getByText('6')).toBeInTheDocument();
    const cloud=rows.find(r=>r.textContent?.includes('regression-20261009-190056'))!;
    expect(within(cloud).getByText('169')).toBeInTheDocument();
    expect(within(cloud).getByText('3')).toBeInTheDocument();
  });
  it('separates verified temporary transactions from unverified runtime recovery',()=>{
    render(<EngineeringConsole/>);show('WEIP-01–12');
    const article=screen.getByRole('heading',{name:'WEIP-10 · V1 adapter'}).closest('article')!;
    expect(within(article).getByText('PASS')).toBeInTheDocument();
    expect(within(article).getByText(/Active-store integration and runtime recovery NOT_VERIFIED/)).toBeInTheDocument();
    show('Keputusan manusia');
    expect(screen.getByText(/Transaksi adapter dan rollback pada temporary store sudah diuji/)).toBeInTheDocument();
    expect(screen.queryByText(/kegagalan ingest menyeluruh dan kompensasinya belum dibuktikan/)).not.toBeInTheDocument();
  });
  it('never counts incomplete JUnit as passing and retains later failures',()=>{
    render(<EngineeringConsole/>);show('Tes & Bukti');
    expect(screen.getByText(/JUnit tidak lengkap/)).toBeInTheDocument();
    const unavailable=screen.getByRole('heading',{name:'regression-20261009-185326'}).closest('section')!;
    expect(within(unavailable).getByText('NOT_VERIFIED')).toBeInTheDocument();
    expect(within(unavailable).queryByText('PASS')).not.toBeInTheDocument();
    const rows=screen.getAllByRole('row');
    const failed=rows.find(r=>r.textContent?.includes('regression-20261009-185424'))!;
    expect(within(failed).getByText('FAIL')).toBeInTheDocument();
    const collectionError=rows.find(r=>r.textContent?.includes('regression-20261009-185632'))!;
    expect(within(collectionError).getByText('ERROR')).toBeInTheDocument();
  });
  it('keeps distinct fingerprint scopes and report-bound gate evidence',()=>{
    const reportPath=resolve('..','docs/reports/openrouter-workflow-20261009T184538/IMPLEMENTATION_REPORT.json');
    const provider=evidence.verifiedCapabilities.find(c=>c.id==='OPENROUTER-LANGGRAPH')!;
    if(existsSync(reportPath)){
      const report=JSON.parse(readFileSync(reportPath,'utf8'));
      expect(provider.fingerprint).toBe(report.audit.fingerprint);
      expect(provider.fingerprintScope).toBe(report.audit.note);
    }else{
      expect(provider.fingerprint).toMatch(/^sha256:[a-f0-9]{64}$/);
      expect(provider.fingerprintScope).toContain('Scoped source bytes');
    }
    expect(provider.fingerprint).not.toBe(evidence.diskFingerprint);
    expect(evidence.gates.find(g=>g.id==='WEIP-10')?.reference).toBe('docs/reports/v1-remaining-20261009T182840/EXECUTION_RESULTS.json');
    expect(evidence.exclusionGroups).toHaveLength(2);
  });
  it('explains API and local AI status in Indonesian without implying live health',()=>{
    const fetch=vi.fn(()=>{throw new Error('Network forbidden')});vi.stubGlobal('fetch',fetch);
    render(<EngineeringConsole/>);
    const guide=screen.getByRole('region',{name:'Panduan singkat'});
    expect(within(guide).getByRole('heading',{name:'Status layanan API'})).toBeInTheDocument();
    expect(within(guide).getByRole('heading',{name:'Status AI lokal'})).toBeInTheDocument();
    expect(within(guide).getAllByText('NOT_VERIFIED')).toHaveLength(2);
    expect(within(guide).getByText(/tidak membuktikan layanan API sedang berjalan/)).toBeInTheDocument();
    expect(screen.getByRole('navigation',{name:'Bagian Console'})).toBeInTheDocument();
    for(const name of ['Ringkasan','Tahapan 0–21','Tes & Bukti'])expect(screen.getByRole('button',{name})).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });
  it('records owner-approved offline fixture scope without interpreting reply 1 as approval',()=>{
    render(<EngineeringConsole/>);show('Keputusan manusia');
    expect(screen.getByRole('heading',{name:'Dokumen uji KTP-el'})).toBeInTheDocument();
    expect(screen.getByText(/Owner sudah menyetujui empat file KTP-el/)).toBeInTheDocument();
    expect(screen.queryByText(/Path fixture lokal dan referensi persetujuan belum diberikan/)).not.toBeInTheDocument();
    const approvalPath=resolve('..',evidence.fixtureApproval.reference);
    if(existsSync(approvalPath)){
      const approval=JSON.parse(readFileSync(approvalPath,'utf8').replace(/^\uFEFF/,''));
      expect(approval.owner_message).toBe('setuju sudah sesuai');
      expect(evidence.fixtureApproval.paths).toEqual(approval.exact_fixture_paths);
    }
    expect(evidence.fixtureApproval.status).toBe('OWNER_APPROVED_OFFLINE_FIXTURE_SCOPE');
    expect(evidence.fixtureApproval.paths).toHaveLength(4);
    expect(evidence.fixtureApproval.verificationStatus).toBe('NOT_RUN');
    expect(evidence.fixtureApproval.sourceAuthentication).toBe('NOT_VERIFIED');
    expect(evidence.fixtureApproval.operatorIdentity).toBe('NOT_VERIFIED');
    expect(evidence.fixtureApproval.activeIntegration).toBe('NOT_AUTHORIZED');
  });
});
