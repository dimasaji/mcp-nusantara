import {afterEach,beforeEach,describe,it,expect,vi} from 'vitest';
import {readFileSync,statSync} from 'node:fs';
import {readSnapshotFile} from './snapshot-file';

vi.mock('node:fs',()=>{
  const fs={readFileSync:vi.fn(),statSync:vi.fn()};
  return {default:fs,...fs};
});
beforeEach(()=>{
  vi.stubEnv('CPLANE_SNAPSHOT_FILE','explicit-test-input.json');
  vi.mocked(statSync).mockReturnValue({isFile:()=>true} as ReturnType<typeof statSync>);
  vi.mocked(readFileSync).mockReturnValue('{"testPayload":"reader-contract"}');
});
afterEach(()=>{vi.resetAllMocks();vi.unstubAllEnvs();});
describe('explicit snapshot prerequisites',()=>{
  it('rejects missing input without selecting a local fallback',()=>{
    vi.stubEnv('CPLANE_SNAPSHOT_FILE','');
    expect(()=>readSnapshotFile()).toThrow('CPLANE_SNAPSHOT_FILE: path is not configured');
    expect(readFileSync).not.toHaveBeenCalled();
  });
  it('rejects absent files with a prerequisite message',()=>{
    vi.mocked(statSync).mockImplementation(()=>{throw new Error('ENOENT');});
    expect(()=>readSnapshotFile()).toThrow('file unavailable');
    expect(readFileSync).not.toHaveBeenCalled();
  });
  it('rejects directories',()=>{
    vi.mocked(statSync).mockReturnValue({isFile:()=>false} as ReturnType<typeof statSync>);
    expect(()=>readSnapshotFile()).toThrow('file unavailable');
  });
  it('rejects unreadable files',()=>{
    vi.mocked(readFileSync).mockImplementation(()=>{throw new Error('EACCES');});
    expect(()=>readSnapshotFile()).toThrow('file unreadable');
  });
  it('rejects invalid JSON without exposing the content',()=>{
    vi.mocked(readFileSync).mockReturnValue('private malformed content');
    expect(()=>readSnapshotFile()).toThrow('invalid JSON');
    try{readSnapshotFile();}catch(error){expect(String(error)).not.toContain('private malformed content');}
  });
  it('reads explicit JSON without promoting or rewriting it',()=>{
    expect(readSnapshotFile()).toEqual({testPayload:'reader-contract'});
    expect(readFileSync).toHaveBeenCalledWith(expect.stringContaining('explicit-test-input.json'),'utf8');
  });
  it('accepts a UTF-8 BOM',()=>{
    vi.mocked(readFileSync).mockReturnValue('\uFEFF{"testPayload":"reader-contract"}');
    expect(readSnapshotFile()).toEqual({testPayload:'reader-contract'});
  });
  it('requires attestation evidence independently of the normal snapshot',()=>{
    vi.stubEnv('R2_CPLANE_ISOLATED_EVIDENCE','');
    expect(()=>readSnapshotFile('R2_CPLANE_ISOLATED_EVIDENCE')).toThrow('R2_CPLANE_ISOLATED_EVIDENCE: path is not configured');
  });
});
