import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {SOPMetadataForm} from '../src/sop-metadata';

afterEach(cleanup);
const absent={status:'unreadable' as const,value:null,page_number:null,note:''};
const metadata={schema_version:1 as const,logical_sop_id:'SOP:fixture',replaces_document_id:null,validity:'not_confirmed' as const,validity_note:'Tidak menyimpulkan hukum.',
  official_title:{status:'present' as const,value:'LAYANAN CONTOH',page_number:1,note:''},
  institution:absent,unit:absent,sop_number:{status:'present' as const,value:'ABC-07',page_number:1,note:''},
  jurisdiction:absent,issued_on:absent,effective_on:absent,expires_on:absent,revision:absent};
it('reads stored backend metadata and saves a correction without retyping detected values',()=>{
  const save=vi.fn();
  render(<SOPMetadataForm documentId="DOC-fixture" metadata={metadata} origin="system" pdf busy={false} onSave={save}/>);
  fireEvent.click(screen.getByText(/Metadata SOP/));
  expect(screen.getByLabelText('Judul resmi SOP',{exact:true})).toHaveValue('LAYANAN CONTOH');
  expect(screen.getByLabelText('Halaman judul')).toHaveValue(1);
  expect(screen.getByRole('list',{name:'Usulan metadata hasil baca'})).toHaveTextContent('Nomor SOP: ABC-07');
  expect(screen.getByRole('list',{name:'Usulan metadata hasil baca'})).toHaveTextContent('Tidak terdeteksi');
  expect(screen.getByRole('button',{name:'Simpan pemeriksaan metadata'})).toBeEnabled();
  fireEvent.click(screen.getByRole('button',{name:'Simpan pemeriksaan metadata'}));
  expect(save).toHaveBeenCalledWith(metadata,null);
});
it('does not show local detection as though it were persisted backend metadata',()=>{
  render(<SOPMetadataForm documentId="DOC-fixture" metadata={metadata} pdf busy={false} extractedBlocks={[{page_numbers:[1],content:'Nama SOP: JUDUL LAIN'}]} onSave={vi.fn()}/>);
  fireEvent.click(screen.getByText(/Metadata SOP/));
  expect(screen.getByLabelText('Judul resmi SOP',{exact:true})).toHaveValue('LAYANAN CONTOH');
  expect(screen.queryByText('JUDUL LAIN')).toBeNull();
});

it('disables metadata controls while a save is in flight',()=>{
  render(<SOPMetadataForm documentId="DOC-fixture" pdf busy onSave={vi.fn()}/>);
  expect(screen.getByLabelText('Identitas layanan SOP')).toBeDisabled();
  expect(screen.getByLabelText('Judul resmi SOP',{exact:true})).toBeDisabled();
  expect(screen.getByRole('button',{name:'Simpan pemeriksaan metadata'})).toBeDisabled();
});
