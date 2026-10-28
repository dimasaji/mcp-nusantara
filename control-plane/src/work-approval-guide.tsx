import type {ExecutionContext} from './api';

/** Explain the server's protocol without treating a stage label as a receipt. */
export function WorkApprovalGuide({context}:{context?:ExecutionContext}){
 const workflow=context?.workflow;
 if(!workflow)return <section className="panel" aria-label="Alur persetujuan pekerjaan"><h2>Alur persetujuan pekerjaan</h2><p>Panduan alur belum diterima dari backend. Muat rencana dan gunakan backend yang menyediakan kontrak alur. Persetujuan tetap mengikuti pemeriksaan server.</p></section>;
 return <section className="panel" aria-label="Alur persetujuan pekerjaan">
  <h2>Alur persetujuan pekerjaan</h2>
  <p>Panel ini meninjau rencana perubahan berkas yang sudah disiapkan. Sumber pekerjaan: <strong>{workflow.source}</strong>.</p>
  <p>{context.plan_origin?.kind==='DEVELOPER_OPERATION'?'Rencana disiapkan melalui operasi developer.':'Asal pembuat rencana ini belum tercatat.'} Identitas personal pembuat belum tercatat.</p>
  <ol className="work-approval-flow">{workflow.steps.map(step=><li key={step.id}>{step.label}</li>)}</ol>
  <p>Urutan di atas adalah alur acuan. Status selesai tetap harus dibuktikan oleh hasil pemeriksaan dan audit.</p>
  <p><strong>Setujui tidak langsung menjalankan pekerjaan.</strong> Gunakan tindakan Jalankan secara terpisah. Persetujuan berlaku {workflow.approval_validity_seconds/60} menit untuk rencana yang cocok dan satu percobaan berizin; backend memeriksa ulang seluruh prasyarat.</p>
  <details><summary>Tanggung jawab tahap dan arti keputusan</summary>
   {workflow.steps.map(step=><div key={step.id}><h3>{step.label}</h3><p>Penanggung jawab: {step.actor}. {step.description}</p></div>)}
   {workflow.decisions.map(decision=><p key={decision.code}><strong>{decision.label}:</strong> {decision.description}</p>)}
  </details>
  <p>Pemeriksaan dan pengesahan SOP tersedia di halaman Dokumen. Panel ini belum menjadi antrean seluruh pekerjaan chat atau Docling.</p>
 </section>;
}
