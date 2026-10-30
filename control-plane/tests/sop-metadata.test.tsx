import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {SOPMetadataForm} from '../src/sop-metadata';

afterEach(cleanup);
it('prefills SOP metadata from extracted text and saves without manual re-entry',()=>{
  const save=vi.fn();
  const extractedBlocks=[{page_numbers:[1],content:[
    'Judul SOP: PERMOHONAN DATA PRIBADI',
    'Instansi: Dinas Kependudukan dan Pencatatan Sipil',
    'Unit Kerja: Bidang Pelayanan',
    'Nomor SOP: 01/SOP-DISDUKCAPIL/2026',
    'Wilayah Kewenangan: Kota Tangerang',
    'Tanggal Penetapan: 12 Oktober 2025',
    'Tanggal Mulai Berlaku: 2025-11-01',
    'Tanggal Akhir Berlaku: 2026-10-31',
    'Nomor Revisi: 2',
  ].join('\n')}];
  render(<SOPMetadataForm documentId="DOC-fixture" pdf busy={false} extractedBlocks={extractedBlocks} onSave={save}/>);
  expect(screen.getByLabelText('Judul resmi SOP',{exact:true})).toHaveValue('PERMOHONAN DATA PRIBADI');
  expect(screen.getByLabelText('Halaman judul')).toHaveValue(1);
  expect((screen.getByLabelText('Identitas layanan SOP') as HTMLInputElement).value).toMatch(/^SOP:/);
  expect(screen.getByRole('button',{name:'Simpan pemeriksaan metadata'})).toBeEnabled();
  expect(screen.getByRole('list',{name:'Usulan metadata hasil baca'})).toHaveTextContent('Nomor SOP');
  fireEvent.click(screen.getByRole('button',{name:'Simpan pemeriksaan metadata'}));
  expect(save).toHaveBeenCalledWith(expect.objectContaining({
    official_title:expect.objectContaining({value:'PERMOHONAN DATA PRIBADI',page_number:1}),
    sop_number:expect.objectContaining({value:'01/SOP-DISDUKCAPIL/2026',page_number:1}),
    issued_on:expect.objectContaining({value:'2025-10-12'}),
    effective_on:expect.objectContaining({value:'2025-11-01'}),
    expires_on:expect.objectContaining({value:'2026-10-31'}),
    validity:'not_confirmed'
  }),null);
});

it('disables metadata controls while a save is in flight',()=>{
  render(<SOPMetadataForm documentId="DOC-fixture" pdf busy onSave={vi.fn()}/>);
  expect(screen.getByLabelText('Identitas layanan SOP')).toBeDisabled();
  expect(screen.getByLabelText('Judul resmi SOP',{exact:true})).toBeDisabled();
  expect(screen.getByRole('button',{name:'Simpan pemeriksaan metadata'})).toBeDisabled();
});
