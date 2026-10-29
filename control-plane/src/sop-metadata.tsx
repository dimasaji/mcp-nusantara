import {useState} from 'react';

const fields={official_title:'Judul resmi SOP',institution:'Instansi',unit:'Unit kerja',sop_number:'Nomor SOP',jurisdiction:'Wilayah kewenangan',issued_on:'Tanggal penetapan',effective_on:'Tanggal mulai berlaku',expires_on:'Tanggal akhir berlaku',revision:'Nomor revisi'};
type FieldName=keyof typeof fields;
type Fact={status:'present'|'not_stated'|'unreadable';value:string|null;page_number:number|null;note:string};
export type OfficialMetadata={schema_version:1;logical_sop_id:string;replaces_document_id:string|null;validity:'not_confirmed'|'confirmed_current'|'withdrawn'|'superseded';validity_note:string}&Record<FieldName,Fact>;

export function SOPMetadataForm({documentId,metadata,eventId,pdf,busy,onSave}:{documentId:string;metadata?:OfficialMetadata|null;eventId?:string|null;pdf:boolean;busy:boolean;onSave:(metadata:OfficialMetadata,eventId:string|null)=>void}){
  const [draft,setDraft]=useState<OfficialMetadata>(()=>metadata??{
    schema_version:1,logical_sop_id:documentId,replaces_document_id:null,validity:'not_confirmed',validity_note:'',
    ...Object.fromEntries(Object.keys(fields).map(key=>[key,{status:key==='official_title'?'present':'unreadable',value:null,page_number:null,note:''}]))
  } as OfficialMetadata);
  const complete=!!draft.logical_sop_id.trim()&&!!draft.validity_note.trim()&&Object.entries(fields).every(([key])=>{
    const fact=draft[key as FieldName];
    return fact.status==='present'?!!fact.value?.trim()&&(!pdf||!!fact.page_number):!!fact.note.trim();
  })&&draft.official_title.status==='present';
  function update(key:FieldName,change:Partial<Fact>){setDraft(old=>({...old,[key]:{...old[key],...change}}));}
  return <details open={!metadata}><summary>Metadata resmi SOP — {metadata?'sudah diperiksa':'perlu diperiksa'}</summary>
    <p>Salin informasi dari sumber asli. Nama file hanya petunjuk. Pilih “Tidak tercantum” atau “Tidak terbaca” beserta alasannya jika informasi tidak tersedia. Tanggal menggunakan YYYY-MM-DD.</p>
    <p>Persetujuan isi mengizinkan penggunaan dokumen; keberlakuan hukum perlu dikonfirmasi tersendiri.</p>
    <fieldset disabled={busy}><legend>Identitas dan sumber metadata</legend>
      <label>Identitas layanan SOP<input value={draft.logical_sop_id} maxLength={128} onChange={e=>setDraft({...draft,logical_sop_id:e.target.value})}/></label>
      <p>Gunakan identitas layanan yang sama untuk PDF revisi SOP yang sama.</p>
      <label>ID dokumen revisi sebelumnya, jika ada<input value={draft.replaces_document_id??''} maxLength={256} onChange={e=>setDraft({...draft,replaces_document_id:e.target.value||null})}/></label>
      <p>Hubungan revisi tidak mencabut dokumen lama secara otomatis. Cabut versi aktif sebelumnya sebelum menyetujui penggantinya.</p>
      {(Object.entries(fields) as [FieldName,string][]).map(([key,label])=><fieldset key={key}><legend>{label}</legend>
        <label>Status {label}<select value={draft[key].status} onChange={e=>update(key,{status:e.target.value as Fact['status'],value:null,page_number:null,note:''})}>
          <option value="present">Tercantum</option><option value="not_stated">Tidak tercantum</option><option value="unreadable">Tidak terbaca</option>
        </select></label>
        {draft[key].status==='present'?<><label>{label}<input value={draft[key].value??''} maxLength={1024} onChange={e=>update(key,{value:e.target.value||null})}/></label>
          {pdf&&<label>Halaman sumber {label}<input type="number" min={1} step={1} value={draft[key].page_number??''} onChange={e=>update(key,{page_number:e.target.value?Number(e.target.value):null})}/></label>}</>:
          <label>Alasan {label}<input value={draft[key].note} maxLength={2000} onChange={e=>update(key,{note:e.target.value})}/></label>}
      </fieldset>)}
      <label>Keberlakuan SOP<select value={draft.validity} onChange={e=>setDraft({...draft,validity:e.target.value as OfficialMetadata['validity']})}>
        <option value="not_confirmed">Belum dikonfirmasi</option><option value="confirmed_current">Dikonfirmasi masih berlaku oleh operator</option><option value="withdrawn">Sudah dicabut</option><option value="superseded">Sudah digantikan</option>
      </select></label>
      <label>Dasar atau keterbatasan konfirmasi keberlakuan<textarea value={draft.validity_note} maxLength={2000} onChange={e=>setDraft({...draft,validity_note:e.target.value})}/></label>
      <button disabled={!complete} onClick={()=>onSave(draft,eventId??null)}>Simpan pemeriksaan metadata</button>
      {!complete&&<p>Lengkapi judul resmi, identitas layanan, sumber atau alasan setiap metadata, serta catatan keberlakuan.</p>}
    </fieldset>
  </details>;
}
