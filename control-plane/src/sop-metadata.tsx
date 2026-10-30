import {useState} from 'react';

const fields={official_title:'Judul resmi SOP',institution:'Instansi',unit:'Unit kerja',sop_number:'Nomor SOP',jurisdiction:'Wilayah kewenangan',issued_on:'Tanggal penetapan',effective_on:'Tanggal mulai berlaku',expires_on:'Tanggal akhir berlaku',revision:'Nomor revisi'};
type FieldName=keyof typeof fields;
type Fact={status:'present'|'not_stated'|'unreadable';value:string|null;page_number:number|null;note:string};
export type OfficialMetadata={schema_version:1;logical_sop_id:string;replaces_document_id:string|null;validity:'not_confirmed'|'confirmed_current'|'withdrawn'|'superseded';validity_note:string}&Record<FieldName,Fact>;
type ExtractedBlock={content:string;page_numbers:number[]};

const labelPatterns:Partial<Record<FieldName,RegExp[]>>={
  official_title:[/^\s*(?:judul(?: resmi)?(?: sop)?|nama sop)\s*[:：-]\s*(.+?)\s*$/i],
  institution:[/^\s*(?:instansi|nama instansi|kementerian|lembaga|perangkat daerah|pemerintah daerah)\s*[:：-]\s*(.+?)\s*$/i],
  unit:[/^\s*(?:unit kerja|unit organisasi|unit pelaksana|bidang|bagian)\s*[:：-]\s*(.+?)\s*$/i],
  sop_number:[/^\s*(?:nomor|no\.?|nomor dokumen)\s*(?:sop|standar operasional prosedur)\s*[:：-]\s*(.+?)\s*$/i,/^\s*(?:nomor|no\.?)\s*[:：-]\s*(.+?)\s*$/i],
  jurisdiction:[/^\s*(?:wilayah kewenangan|wilayah kerja|cakupan wilayah)\s*[:：-]\s*(.+?)\s*$/i],
  issued_on:[/^\s*(?:tanggal penetapan|ditetapkan pada|tanggal ditetapkan)\s*[:：-]\s*(.+?)\s*$/i],
  effective_on:[/^\s*(?:tanggal mulai berlaku|mulai berlaku|berlaku mulai|tanggal berlaku)\s*[:：-]\s*(.+?)\s*$/i],
  expires_on:[/^\s*(?:tanggal akhir berlaku|berlaku sampai|berlaku hingga|tanggal berakhir)\s*[:：-]\s*(.+?)\s*$/i],
  revision:[/^\s*(?:nomor revisi|revisi(?: ke)?|revisi)\s*[:：-]\s*(.+?)\s*$/i],
};
function cleanValue(value:string){return value.replace(/\s{2,}/g,' ').replace(/[;|]+$/,'').trim().slice(0,1024);}
function normalizeDate(value:string){
  const text=value.trim();
  const months:Record<string,string>={januari:'01',februari:'02',maret:'03',april:'04',mei:'05',juni:'06',juli:'07',agustus:'08',september:'09',oktober:'10',november:'11',desember:'12'};
  const iso=text.match(/\b(\d{4})-(\d{1,2})-(\d{1,2})\b/);
  const local=text.match(/\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b/);
  const named=text.match(/\b(\d{1,2})\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s+(\d{4})\b/i);
  const result=iso?`${iso[1]}-${iso[2].padStart(2,'0')}-${iso[3].padStart(2,'0')}`:
    local?`${local[3]}-${local[2].padStart(2,'0')}-${local[1].padStart(2,'0')}`:
    named?`${named[3]}-${months[named[2].toLocaleLowerCase('id')]}-${named[1].padStart(2,'0')}`:null;
  if(!result)return '';
  const [year,month,day]=result.split('-').map(Number);
  const parsed=new Date(Date.UTC(year,month-1,day));
  return parsed.getUTCFullYear()===year&&parsed.getUTCMonth()===month-1&&parsed.getUTCDate()===day?result:'';
}
function findFact(key:FieldName,blocks:ExtractedBlock[]):Fact{
  for(const block of blocks){
    for(const line of block.content.split(/\r?\n/)){
      for(const pattern of labelPatterns[key]??[]){
        const match=line.match(pattern);
        if(match?.[1]){
          const value=cleanValue(key.endsWith('_on')?normalizeDate(match[1]):match[1]);
          if(value)return {status:'present',value,page_number:block.page_numbers[0]??null,note:''};
        }
      }
    }
  }
  if(key==='official_title'){
    const lines=blocks.flatMap(block=>block.content.split(/\r?\n/).map(line=>({line:line.trim(),page:block.page_numbers[0]??null})))
      .filter(item=>item.page===null||item.page<=2);
    for(let i=0;i<lines.length;i++){
      const heading=lines[i].line;
      const inline=heading.match(/^\s*(?:standar operasional prosedur|s\.?o\.?p\.?)\s*[:：-]?\s+(.+)$/i);
      if(inline?.[1]&&inline[1].trim().length>=8){
        return {status:'present',value:cleanValue(inline[1]),page_number:lines[i].page,note:''};
      }
      if(/standar operasional prosedur|^s\.?o\.?p\.?$/i.test(heading)){
        for(let j=i+1;j<Math.min(lines.length,i+5);j++){
          const candidate=lines[j].line;
          if(candidate.length<8||candidate.length>180||/^(?:PEMERINTAH|DINAS|KECAMATAN|KELURAHAN|NOMOR|TANGGAL|HALAMAN)\b/i.test(candidate))continue;
          const letters=candidate.replace(/[^A-Za-zÀ-ÿ]/g,'');
          if(letters.length>=8&&letters===letters.toLocaleUpperCase('id')){
            return {status:'present',value:cleanValue(candidate),page_number:lines[j].page,note:''};
          }
        }
      }
    }
  }
  return {status:'unreadable',value:null,page_number:null,note:'Belum terdeteksi otomatis pada hasil ekstraksi. Sistem tidak menyimpulkan informasi ini tidak tercantum.'};
}
function makeLogicalId(facts:Record<FieldName,Fact>,documentId:string){
  const number=facts.sop_number.value;
  const anchors=number?[facts.institution.value,facts.unit.value,number]:[facts.institution.value,facts.unit.value,facts.official_title.value];
  const slug=anchors.filter((value):value is string=>!!value?.trim()).join('-')
    .normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,120);
  return slug?`SOP:${slug}`:documentId;
}
function suggestMetadata(documentId:string,blocks:ExtractedBlock[]):OfficialMetadata{
  const facts=Object.fromEntries((Object.keys(fields) as FieldName[]).map(key=>[key,findFact(key,blocks)])) as Record<FieldName,Fact>;
  return {
    schema_version:1,logical_sop_id:makeLogicalId(facts,documentId),replaces_document_id:null,
    validity:'not_confirmed',validity_note:'Belum dikonfirmasi dari sumber resmi; pemeriksaan isi dokumen tetap dapat dilanjutkan.',
    ...facts,
  };
}

export function SOPMetadataForm({documentId,metadata,eventId,pdf,busy,extractedBlocks=[],onSave}:{documentId:string;metadata?:OfficialMetadata|null;eventId?:string|null;pdf:boolean;busy:boolean;extractedBlocks?:ExtractedBlock[];onSave:(metadata:OfficialMetadata,eventId:string|null)=>void}){
  const [draft,setDraft]=useState<OfficialMetadata>(()=>metadata??suggestMetadata(documentId,extractedBlocks));
  const detected=(Object.keys(fields) as FieldName[]).filter(key=>draft[key].status==='present').length;
  const complete=!!draft.logical_sop_id.trim()&&!!draft.validity_note.trim()&&(Object.keys(fields) as FieldName[]).every(key=>{
    const fact=draft[key];
    return fact.status==='present'?!!fact.value?.trim()&&(!pdf||!!fact.page_number):!!fact.note.trim();
  })&&draft.official_title.status==='present';
  function update(key:FieldName,change:Partial<Fact>){setDraft(old=>({...old,[key]:{...old[key],...change}}));}
  return <details open={!metadata}><summary>Metadata resmi SOP — {metadata?'sudah diperiksa':'siap ditinjau'}</summary>
    <p>Sistem menyarankan {detected} dari {Object.keys(fields).length} usulan dari hasil baca PDF. Halaman sumber terisi otomatis. Periksa ringkasan dan ubah hanya jika ada yang keliru.</p>
    <p>Persetujuan isi mengizinkan penggunaan dokumen; keberlakuan hukum tetap terpisah dan tidak disimpulkan oleh AI.</p>
    <fieldset disabled={busy}><legend>Ringkasan metadata</legend>
      <label>Judul resmi SOP<input value={draft.official_title.value??''} maxLength={1024} placeholder="Sistem mengisi jika judul terbaca jelas pada PDF" onChange={e=>setDraft(old=>{const next={...old,official_title:{...old.official_title,status:'present' as const,value:e.target.value||null}};if(!metadata&&(old.logical_sop_id===documentId||old.logical_sop_id.startsWith('SOP:')))next.logical_sop_id=makeLogicalId(next,documentId);return next;})}/></label>
      {pdf&&<label>Halaman judul<input type="number" min={1} step={1} value={draft.official_title.page_number??''} onChange={e=>update('official_title',{page_number:e.target.value?Number(e.target.value):null})}/></label>}
      {draft.official_title.status!=='present'&&<p>Judul belum dapat dikenali otomatis. Isi judul resmi dari PDF; tidak perlu menyalin metadata lainnya.</p>}
      <p>Identitas layanan SOP dibuat otomatis: <strong>{draft.logical_sop_id}</strong></p>
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
      <button disabled={!complete} onClick={()=>onSave(draft,eventId??null)}>Konfirmasi metadata yang disarankan</button>
      {!complete&&<p>Judul resmi belum tersedia. Isi atau koreksi judul dan halaman sumbernya.</p>}
    </fieldset>
  </details>;
}
