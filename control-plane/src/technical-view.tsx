import {useState,type ReactNode} from 'react';
import {Link} from '@tanstack/react-router';

/** Presentation only. Backend authorization and acceptance rules remain authoritative. */
export function TechnicalView({children}:{children:ReactNode}){
  const [open,setOpen]=useState(false);
  return <>
    <section className="panel" aria-label="Detail sistem">
      <h1>Detail sistem</h1>
      <p>Untuk pekerjaan sehari-hari, gunakan Beranda, Dokumen, atau Persetujuan. Kode pemeriksaan dan bukti engineering tersedia saat diperlukan.</p>
      <nav className="op-button-row" aria-label="Pekerjaan operator"><Link to="/dashboard">Beranda</Link><Link to="/knowledge">Dokumen</Link><Link to="/approvals">Persetujuan</Link></nav>
      <button type="button" aria-expanded={open} onClick={()=>setOpen(value=>!value)}>{open?'Tutup detail teknis':'Buka detail teknis'}</button>
      <p>Pilihan tampilan ini tidak memberikan izin tambahan atau mengubah hasil pemeriksaan.</p>
    </section>
    {open&&<section aria-label="Pemeriksaan teknis">{children}</section>}
  </>;
}
