import {useState} from 'react';

const fields={official_title:'Judul resmi SOP',institution:'Instansi',unit:'Unit kerja',sop_number:'Nomor SOP',jurisdiction:'Wilayah kewenangan',issued_on:'Tanggal penetapan',effective_on:'Tanggal mulai berlaku',expires_on:'Tanggal akhir berlaku',revision:'Nomor revisi'};
type FieldName=keyof typeof fields;
type Fact={status:'present'|'not_stated'|'unreadable';value:string|null;page_number:number|null;note:string};
export type OfficialMetadata={schema_version:1;logical_sop_id:string;replaces_document_id:string|null;validity:'not_confirmed'|'confirmed_current'|'withdrawn'|'superseded';validity_note:string}&Record<FieldName,Fact>;
type ExtractedBlock={content:string;page_numbers:number[]};

export function SOPMetadataForm({documentId,metadata,eventId,pdf,busy,origin,onSave}:{documentId:string;origin?:'system'|'operator';metadata?:OfficialMetadata|null;eventId?:string|null;pdf:boolean;busy:boolean;extractedBlocks?:ExtractedBlock[];onSave:(metadata:OfficialMetadata,eventId:string|null)=>void}){
  const [draft,setDraft]=useState<OfficialMetadata>(()=>metadata??{schema_version:1,logical_sop_id:documentId,replaces_document_id:null,validity:'not_confirmed',validity_note:'Keberlakuan hukum tidak disimpulkan oleh sistem.',...Object.fromEntries(Object.keys(fields).map(key=>[key,{status:'unreadable',value:null,page_number:null,note:''}]))} as OfficialMetadata);
  const detected=(Object.keys(fields) as FieldName[]).filter(key=>draft[key].status==='present').length;
  const complete=!!draft.logical_sop_id.trim()&&!!draft.validity_note.trim()&&(Object.keys(fields) as FieldName[]).every(key=>{
    const fact=draft[key];
    return fact.status==='present'?!!fact.value?.trim()&&(!pdf||!!fact.page_number):true;
  })&&draft.official_title.status==='present';
  function update(key:FieldName,change:Partial<Fact>){setDraft(old=>({...old,[key]:{...old[key],...change}}));}
  return <details><summary>Metadata SOP - {metadata?'tersimpan di backend':'perlu koreksi judul'}</summary>
    <p>{origin==='operator'?'Koreksi operator tersimpan.':'Hasil deteksi sistem tersimpan untuk versi ini.'} Cocokkan dengan halaman sumber; koreksi hanya nilai yang salah.</p>
    <ul aria-label="Usulan metadata hasil baca">{(Object.entries(fields) as [FieldName,string][]).map(([key,label])=><li key={key}><strong>{label}:</strong> {draft[key].status==='present'?draft[key].value:draft[key].status==='not_stated'?'Tidak tercantum dalam sumber':'Tidak terdeteksi'} {pdf&&draft[key].page_number&&('/ halaman '+draft[key].page_number)}</li>)}</ul>
    <p>Persetujuan penggunaan di Chat dilakukan sekali pada ringkasan dokumen; keberlakuan hukum tetap terpisah.</p>
    <fieldset disabled={busy}><legend>Ringkasan metadata</legend>
      <label>Judul resmi SOP<input value={draft.official_title.value??''} maxLength={1024} placeholder="Sistem mengisi jika judul terbaca jelas pada PDF" onChange={e=>setDraft(old=>{const next={...old,official_title:{...old.official_title,status:'present' as const,value:e.target.value||null}};return next;})}/></label>
      {pdf&&<label>Halaman judul<input type="number" min={1} step={1} value={draft.official_title.page_number??''} onChange={e=>update('official_title',{page_number:e.target.value?Number(e.target.value):null})}/></label>}
      {draft.official_title.status!=='present'&&<p>Judul belum dapat dikenali otomatis. Isi judul resmi dari PDF; tidak perlu menyalin metadata lainnya.</p>}
      <label>Identitas layanan SOP<input value={draft.logical_sop_id} readOnly aria-readonly="true"/></label>
      <p>ID layanan dibuat otomatis dari metadata yang ditemukan dan tetap dapat dikoreksi melalui pengelolaan revisi.</p>
      <label>Keberlakuan SOP<select value={draft.validity} onChange={e=>{const validity=e.target.value as OfficialMetadata['validity'];setDraft({...draft,validity,validity_note:validity==='not_confirmed'?'Belum dikonfirmasi dari sumber resmi; pemeriksaan isi dokumen tetap dapat dilanjutkan.':''});}}> 
        <option value="not_confirmed">Belum dikonfirmasi</option><option value="confirmed_current">Dikonfirmasi masih berlaku oleh operator</option><option value="withdrawn">Sudah dicabut</option><option value="superseded">Sudah digantikan</option>
      </select></label>
      {draft.validity==='not_confirmed'?<p>Sistem tidak meminta operator mengetik alasan. Status hukum tetap belum dikonfirmasi.</p>:<label>Dasar konfirmasi keberlakuan<textarea value={draft.validity_note} maxLength={2000} onChange={e=>setDraft({...draft,validity_note:e.target.value})}/></label>}
      <details><summary>Periksa atau koreksi rincian metadata ({detected} ditemukan otomatis)</summary>
        <label>ID dokumen revisi sebelumnya, jika ada<input value={draft.replaces_document_id??''} maxLength={256} onChange={e=>setDraft({...draft,replaces_document_id:e.target.value||null})}/></label>
        <p>Biarkan kosong jika bukan revisi. Sistem tidak mencabut SOP lama secara otomatis.</p>
        {(Object.entries(fields) as [FieldName,string][]).filter(([key])=>key!=='official_title').map(([key,label])=><fieldset key={key}><legend>{label}</legend>
          <label>Status {label}<select value={draft[key].status} onChange={e=>update(key,{status:e.target.value as Fact['status'],value:null,page_number:null,note:e.target.value==='present'?'':'Informasi belum dikonfirmasi dari PDF.'})}>
            <option value="present">Tercantum</option><option value="not_stated">Tidak tercantum</option><option value="unreadable">Tidak terbaca</option>
          </select></label>
          {draft[key].status==='present'?<><label>{label}<input value={draft[key].value??''} maxLength={1024} onChange={e=>update(key,{value:e.target.value||null})}/></label>
            {pdf&&<label>Halaman sumber {label}<input type="number" min={1} step={1} value={draft[key].page_number??''} onChange={e=>update(key,{page_number:e.target.value?Number(e.target.value):null})}/></label>}</>:
            <label>Catatan (diisi otomatis; ubah bila perlu)<input value={draft[key].note} maxLength={2000} onChange={e=>update(key,{note:e.target.value})}/></label>}
        </fieldset>)}
        <p>Gunakan identitas layanan yang sama untuk PDF revisi SOP yang sama.</p>
      </details>
      <button disabled={!complete} onClick={()=>onSave(draft,eventId??null)}>Simpan pemeriksaan metadata</button>
      {!complete&&<p>{draft.official_title.status!=='present'||!draft.official_title.value?'Isi judul resmi dari PDF.':pdf&&!draft.official_title.page_number?'Tambahkan halaman PDF yang menjadi sumber judul.':'Lengkapi metadata yang belum valid.'}</p>}
    </fieldset>
  </details>;
}
