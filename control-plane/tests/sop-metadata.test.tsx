import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {SOPMetadataForm} from '../src/sop-metadata';

afterEach(cleanup);
it('requires an official title, page and an explicit reason for unavailable fields',()=>{
  const save=vi.fn();
  render(<SOPMetadataForm documentId="DOC-fixture" pdf busy={false} onSave={save}/>);
  expect(screen.getByLabelText('Judul resmi SOP',{exact:true})).toHaveValue('');
  const button=screen.getByRole('button',{name:'Simpan pemeriksaan metadata'});
  expect(button).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Judul resmi SOP',{exact:true}),{target:{value:'PERMOHONAN DATA PRIBADI'}});
  fireEvent.change(screen.getByLabelText('Halaman sumber Judul resmi SOP'),{target:{value:'1'}});
  for(const label of ['Instansi','Unit kerja','Nomor SOP','Wilayah kewenangan','Tanggal penetapan','Tanggal mulai berlaku','Tanggal akhir berlaku','Nomor revisi']){
    fireEvent.change(screen.getByLabelText(`Status ${label}`),{target:{value:'not_stated'}});
    fireEvent.change(screen.getByLabelText(`Alasan ${label}`),{target:{value:'Tidak tercantum pada PDF yang diperiksa.'}});
  }
  fireEvent.change(screen.getByLabelText('Dasar atau keterbatasan konfirmasi keberlakuan'),{target:{value:'Belum dikonfirmasi ke instansi.'}});
  expect(button).toBeEnabled();fireEvent.click(button);
  expect(save).toHaveBeenCalledWith(expect.objectContaining({
    logical_sop_id:'DOC-fixture',official_title:expect.objectContaining({value:'PERMOHONAN DATA PRIBADI',page_number:1}),
    institution:expect.objectContaining({status:'not_stated',value:null}),validity:'not_confirmed'
  }),null);
});

it('disables every metadata control while a save is in flight',()=>{
  render(<SOPMetadataForm documentId="DOC-fixture" pdf busy onSave={vi.fn()}/>);
  expect(screen.getByLabelText('Identitas layanan SOP')).toBeDisabled();
  expect(screen.getByRole('button',{name:'Simpan pemeriksaan metadata'})).toBeDisabled();
});
