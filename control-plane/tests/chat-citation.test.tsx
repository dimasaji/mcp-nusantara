import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {ChatCitation} from '../src/chat-citation';

const evidence={document_id:'DOC-1',title:'SOP contoh',chunk:'',score:1,pages:[2],block_ids:[]};
afterEach(()=>{cleanup();vi.unstubAllGlobals();});

it('opens the cited PDF page with session headers and releases the blob on unmount',async()=>{
  URL.createObjectURL=vi.fn(()=> 'blob:source');URL.revokeObjectURL=vi.fn();
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,headers:new Headers({'Content-Type':'application/pdf'}),blob:async()=>new Blob(['%PDF-fixture'])})));
  render(<ChatCitation evidence={evidence} requestId={'a'.repeat(32)} session="web-test-session" token="private-token"/>);
  fireEvent.click(screen.getByText('SOP contoh'));
  fireEvent.click(screen.getByRole('button',{name:'Buka halaman 2'}));
  await screen.findByTitle('PDF SOP contoh halaman 2');
  expect(screen.getByTitle('PDF SOP contoh halaman 2')).toHaveAttribute('src','blob:source#page=2');
  const [url,options]=vi.mocked(fetch).mock.calls[0];
  expect(String(url)).toContain('request_id='+'a'.repeat(32));
  expect(String(url)).not.toContain('private-token');
  expect(options?.headers).toEqual({'X-Admin-Token':'private-token','X-Chat-Session':'web-test-session'});
  cleanup();expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:source');
});

it('explains a changed source and offers retry without opening the latest PDF',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:false,status:409})));
  render(<ChatCitation evidence={evidence} requestId={'a'.repeat(32)} session="web-test-session" token="private-token"/>);
  fireEvent.click(screen.getByText('SOP contoh'));
  fireEvent.click(screen.getByRole('button',{name:'Buka halaman 2'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Versi atau persetujuan sumber berubah');
  expect(screen.queryByTitle('PDF SOP contoh halaman 2')).not.toBeInTheDocument();
  await waitFor(()=>expect(screen.getByRole('button',{name:'Buka halaman 2'})).toBeEnabled());
});

it('does not open legacy answers without a saved request binding',()=>{
  render(<ChatCitation evidence={evidence} session="web-test-session" token="private-token"/>);
  fireEvent.click(screen.getByText('SOP contoh'));
  expect(screen.getByRole('button',{name:'Buka halaman 2'})).toBeDisabled();
});
it('clears a previously opened source when the saved answer binding changes',async()=>{
  URL.createObjectURL=vi.fn(()=> 'blob:old');URL.revokeObjectURL=vi.fn();
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,headers:new Headers({'Content-Type':'application/pdf'}),blob:async()=>new Blob(['%PDF-fixture'])})));
  const view=render(<ChatCitation evidence={evidence} requestId={'a'.repeat(32)} session="web-test-session" token="private-token"/>);
  fireEvent.click(screen.getByText('SOP contoh'));
  fireEvent.click(screen.getByRole('button',{name:'Buka halaman 2'}));
  await screen.findByTitle('PDF SOP contoh halaman 2');
  view.rerender(<ChatCitation evidence={evidence} requestId={'b'.repeat(32)} session="web-test-session" token="private-token"/>);
  expect(screen.queryByTitle('PDF SOP contoh halaman 2')).not.toBeInTheDocument();
  expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:old');
});
