import type {ExecutionContext} from './api';

/** Describe the backend contract; these stages do not claim execution success. */
export function WorkApprovalGuide({context}:{context?:ExecutionContext}){
  const workflow=context?.workflow;
  return <section className="panel" aria-label="Alur persetujuan pekerjaan">
    <h2>Alur persetujuan pekerjaan</h2>
    {!workflow?<p>Alur pekerjaan belum tersedia dari backend.</p>:<>
      <ol>{workflow.steps.map(step=><li key={step.id}>
        <strong>{step.label}</strong> · {step.actor}<p>{step.description}</p>
      </li>)}</ol>
      <p>Persetujuan tidak langsung menjalankan pekerjaan. Backend memeriksa kembali izin sebelum eksekusi.</p>
      <p>Masa berlaku persetujuan: {workflow.approval_validity_seconds} detik.</p>
      <dl>{workflow.decisions.map(decision=><div key={decision.code}>
        <dt>{decision.label}</dt><dd>{decision.description}</dd>
      </div>)}</dl>
    </>}
  </section>;
}
