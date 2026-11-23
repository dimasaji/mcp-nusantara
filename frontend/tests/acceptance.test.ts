import {describe,it,expect} from 'vitest';
import {readSnapshotFile} from './snapshot-file';
import {SystemHealthSchema} from '../src/schemas';
import {canApprove,counts,emptySession,evidenceKey,gateEvidenceReady,humanCases,limitations,workflow,stages} from '../src/acceptance';
const fixture=()=>SystemHealthSchema.parse(readSnapshotFile());
describe('human authority boundary',()=>{
  it('never copies engineering PASS to human tests',()=>{const s=fixture(),session=emptySession(evidenceKey(s));expect(counts(session)).toEqual({pass:0,fail:0,blocked:0,untested:8});expect(canApprove(s,session)).toBe(false);});
  it('requires complete human PASS, acknowledgements and inspected sources',()=>{
    const s=fixture(),session=emptySession(evidenceKey(s));session.results=Object.fromEntries(humanCases.map(c=>[c.id,'PASS']));expect(canApprove(s,session)).toBe(false);
    session.systemReviewed=true;session.evidenceReviewed=true;session.inspected=s.gates.map(g=>g.id);expect(canApprove(s,session)).toBe(false);session.reviewReviewed=true;expect(canApprove(s,session)).toBe(true);
    session.results.open='FAIL';expect(canApprove(s,session)).toBe(false);session.results.open='BLOCKED';expect(canApprove(s,session)).toBe(false);
  });
  it('does not approve incomplete or hash-unverified gate evidence',()=>{const s=fixture();s.gates.pop();expect(gateEvidenceReady(s)).toBe(false);const other=fixture();other.evidence.find(e=>e.id==='r3')!.sha256=null;expect(gateEvidenceReady(other)).toBe(false);});
  it('ignores refresh timestamps but detects material evidence drift',()=>{const s=fixture(),refresh=structuredClone(s);refresh.timestamp='new capture';expect(evidenceKey(refresh)).toBe(evidenceKey(s));refresh.evidence[0].sha256='changed';expect(evidenceKey(refresh)).not.toBe(evidenceKey(s));});
  it('keeps runtime and protected-file limitations visible',()=>{const s=fixture();s.protected_assets[1].status='NOT_VERIFIED';expect(limitations(s).join(' ')).toContain('Current runtime identity is NOT VERIFIED');expect(limitations(s).join(' ')).toContain(s.protected_assets[1].path);expect(s.runtime.current_status).toBe('NOT_VERIFIED');});
});
describe('sequential stage invariants',()=>{
  it('unlocks exactly one next stage after each completion',()=>{const session=emptySession();expect(workflow(session).available).toEqual({System:true,Evidence:false,Test:false,Review:false,Decision:false});session.systemReviewed=true;expect(workflow(session).available.Evidence).toBe(true);expect(workflow(session).available.Test).toBe(false);session.inspected=Array.from({length:13},(_,i)=>`R3.${i+1}`);session.evidenceReviewed=true;expect(workflow(session).available.Test).toBe(false);session.inspected.push('R3.14');expect(workflow(session).available.Test).toBe(true);expect(workflow(session).available.Review).toBe(false);session.results=Object.fromEntries(humanCases.map((c,i)=>[c.id,i%2?'FAIL':'BLOCKED']));expect(workflow(session).available.Review).toBe(true);expect(workflow(session).available.Decision).toBe(false);session.reviewReviewed=true;expect(workflow(session).available.Decision).toBe(true);expect(workflow(session).complete.Decision).toBe(false);});
  it.each(stages.slice(1))('%s cannot bypass upstream prerequisites even with stale downstream flags',stage=>{const session=emptySession();session.reviewReviewed=true;session.evidenceReviewed=true;session.results=Object.fromEntries(humanCases.map(c=>[c.id,'PASS']));expect(workflow(session).available[stage]).toBe(false);expect(workflow(session).blockers[stage].join(' ')).toContain('System');});
  it('invalid and missing results do not count as explicit human completion',()=>{const session=emptySession();session.systemReviewed=true;session.evidenceReviewed=true;session.inspected=Array.from({length:14},(_,i)=>`R3.${i+1}`);session.results=Object.fromEntries(humanCases.map(c=>[c.id,'PASS']));delete session.results.open;expect(workflow(session).available.Review).toBe(false);session.results.open='NOT TESTED';expect(workflow(session).available.Review).toBe(false);});
});
