import type {EvidencePackage,ExecutionContext,ExecutionHistory,DecisionRecord} from './api';

/**
 * Shared readiness model for /verification and /review-execute.
 *
 * The five facts stay separate on purpose. Evidence validity, plan readiness,
 * operator authentication, decision availability and execution success are
 * different claims; this module never merges them into one "ready" flag.
 */
export type Status='READY'|'BLOCKED'|'UNKNOWN';

export type Check={id:string;label:string;status:Status;detail:string;why:string};

const REASONS:Record<string,string>={
  NO_CURRENT_TEST_RUN:'Belum ada test-run yang dipublikasikan untuk paket bukti ini.',
  TEST_SOURCE_COVERAGE_INCOMPLETE:'Test-run terakhir belum menguji semua source yang dipersyaratkan, jadi belum bisa mewakili source saat ini.',
  TEST_SOURCE_CHANGED_AFTER_RUN:'Source berubah setelah test-run terakhir, sehingga hasil tes lama tidak lagi berlaku untuk source sekarang.',
  TEST_RESULT_COUNTS_FAILED:'Test-run terakhir mencatat kegagalan tes.',
  TEST_RUN_FAILED:'Test-run terakhir gagal, jadi kriteria ini belum terverifikasi.',
  REQUIRED_TEST_RESULT_MISSING:'Ada hasil tes yang diwajibkan untuk kriteria ini tetapi tidak ditemukan.',
  TEST_RESULTS_MISSING:'Berkas hasil tes tidak ditemukan.',
  TEST_RESULTS_ACCESS_DENIED:'Berkas hasil tes tidak dapat dibaca.',
  TEST_RESULTS_HASH_MISMATCH:'Hash berkas hasil tes tidak cocok dengan yang tercatat.',
  TEST_RESULTS_BUNDLE_INVALID:'Bundel hasil tes tidak berbentuk seperti yang diharapkan.',
  TEST_RESULT_ARTIFACT_HASH_MISMATCH:'Hash artefak hasil tes tidak cocok.',
  TEST_ISOLATION_NOT_PROVEN:'Isolasi test-run tidak terbukti, jadi hasilnya belum bisa diterima.',
  TEST_REPORT_INVALID:'Laporan test-run tidak dapat dibaca.',
  TEST_REPORT_FIELDS_INVALID:'Laporan test-run tidak lengkap.',
  TEST_REPORT_SIZE_LIMIT:'Laporan test-run melebihi batas ukuran.',
  EVIDENCE_REQUIREMENTS_MISSING:'Daftar persyaratan bukti tidak ditemukan.',
  EVIDENCE_REQUIREMENTS_INVALID:'Daftar persyaratan bukti tidak valid.',
  ARTIFACT_INVALID:'Artefak bukti tidak valid.',
  NOT_A_REGULAR_FILE:'Jalur bukti bukan berkas biasa.',
  ARTIFACT_READ_FAILED:'Artefak bukti tidak dapat dibaca.',
};

/** Turn a raw server reason code into one plain sentence. */
export function plainReason(reason:string|null|undefined):string{
  if(!reason)return 'Alasan belum dilaporkan server.';
  const known=REASONS[reason];
  if(known)return known;
  if(/^[A-Z0-9_]+$/.test(reason))return `Kode dari server: ${reason.replaceAll('_',' ').toLowerCase()}.`;
  return reason;
}

export type ReadinessInput={
  token:string;
  packageState:{state:Status;pkg?:EvidencePackage;reason?:string};
  planState:{state:Status;context?:ExecutionContext;reason?:string};
  auditState:{state:Status;history?:ExecutionHistory;reason?:string};
};

export type Readiness={
  evidenceValid:boolean;planReady:boolean;operatorAuthenticated:boolean;
  decisionAvailable:boolean;executionReady:boolean;
  activeDecision?:DecisionRecord;staleDecision?:DecisionRecord;
  checks:Check[];
  next:{label:string;to:string;enabled:boolean;why:string};
};

function decisionStatus(record:DecisionRecord):string{
  return `${record.decision} · ${record.decision_id} · ${record.timestamp}`;
}

export function readiness(input:ReadinessInput):Readiness{
  const pkg=input.packageState.pkg;
  const context=input.planState.context;
  const history=input.auditState.history;
  const authenticated=!!input.token.trim()&&input.auditState.state==='READY'&&history?.decision_audit==='VALIDATED_HASH_CHAIN';
  const evidenceValid=input.packageState.state==='READY'&&pkg?.pass_allowed===true&&pkg.blockers.length===0;
  const planReady=input.planState.state==='READY'&&!!context&&!context.completed;

  const records=history?.decisions??[];
  const activeDecision=pkg?records.filter(r=>r.package_id===pkg.package_id).at(-1):undefined;
  const latest=records.at(-1);
  const staleDecision=!activeDecision&&latest&&pkg&&latest.package_id!==pkg.package_id?latest:undefined;
  const decisionAvailable=evidenceValid&&authenticated&&planReady;

  const planMatches=!!activeDecision?.plan_binding&&!!context&&
    activeDecision.plan_binding.version===context.plan_binding.version&&
    activeDecision.plan_binding.plan_id===context.change_id&&activeDecision.plan_binding.action===context.plan_binding.action;
  const age=activeDecision?Date.now()-Date.parse(activeDecision.timestamp):NaN;
  const expired=!Number.isFinite(age)||age<0||age>3_600_000;
  const consumed=!!activeDecision&&!!history?.executions.some(e=>e.decision_id===activeDecision.decision_id&&['AUTHORIZED_ATTEMPT','PASS'].includes(e.result));
  const executionReady=authenticated&&!!activeDecision&&activeDecision.decision==='PASS'&&evidenceValid&&planReady&&planMatches&&!expired&&!consumed;

  const checks:Check[]=[
    {id:'EV',label:'Evidence valid',status:evidenceValid?'READY':input.packageState.state==='UNKNOWN'?'UNKNOWN':'BLOCKED',
      detail:evidenceValid?`${pkg?.criteria.filter(c=>c.status==='VALID').length}/${pkg?.criteria.length} kriteria tervalidasi`
        :pkg?`${pkg.criteria.filter(c=>c.status==='VALID').length}/${pkg.criteria.length} kriteria tervalidasi`
        :'Paket bukti belum terbaca',
      why:evidenceValid?'Semua kriteria punya hasil tes yang terikat pada source saat ini.'
        :input.packageState.reason?plainReason(input.packageState.reason)
        :pkg?.blockers.length?pkg.blockers.map(b=>`${b.id}: ${plainReason(b.reason)}`).join(' ')
        :'Paket bukti belum bisa dinilai.'},
    {id:'PLAN',label:'Plan siap',status:planReady?'READY':input.planState.state==='UNKNOWN'?'UNKNOWN':'BLOCKED',
      detail:context?.completed?'Pekerjaan sudah selesai; periksa hasil di History'
        :planReady&&context?`${context.change_id} · ${context.target_files.length} berkas target · ${context.operation}`
        :'Rencana belum tersedia',
      why:context?.completed?'Backend sudah mencatat keberhasilan rencana ini. Publikasi ulang memerlukan rencana baru.'
        :planReady?'Rencana lengkap: tujuan, perubahan, risiko, pengujian dan pemulihan terbaca.'
        :input.planState.reason?plainReason(input.planState.reason)
        :!input.token.trim()?'Perlu token operator untuk membaca rencana.'
        :'Rencana belum lolos pemeriksaan backend.'},
    {id:'AUTH',label:'Operator terautentikasi',status:authenticated?'READY':input.token.trim()?'BLOCKED':'UNKNOWN',
      detail:authenticated?'Token operator diterima dan audit keputusan terbaca'
        :input.token.trim()?'Token terisi tetapi audit belum terbaca':'Belum ada token operator',
      why:authenticated?'Server menerima kredensial operator dan hash chain audit tervalidasi.'
        :input.token.trim()?plainReason(input.auditState.reason)
        :'Masukkan token operator di Developer Console; tanpa itu keputusan tidak dapat disimpan dan History tidak terbaca.'},
    {id:'DEC',label:'Keputusan tersedia',status:decisionAvailable?'READY':'BLOCKED',
      detail:activeDecision?`Sudah ada keputusan untuk paket ini: ${decisionStatus(activeDecision)}`
        :decisionAvailable?'Belum ada keputusan untuk paket ini'
        :!authenticated?'Menunggu autentikasi operator':'Menunggu bukti valid',
      why:activeDecision?'Keputusan terbaru berlaku; peninjauan ulang tetap dicatat tanpa menghapus riwayat.'
        :decisionAvailable?'PASS/FAIL/HOLD dapat dicatat sekarang. PASS hanya aktif bila bukti valid.'
        :!authenticated?'Keputusan butuh operator terautentikasi.'
        :'PASS terkunci sampai seluruh kriteria valid; FAIL dan HOLD tetap tersedia setelah autentikasi.'},
    {id:'EXEC',label:'Izin eksekusi',status:executionReady?'READY':'BLOCKED',
      detail:consumed?'Keputusan ini sudah dipakai untuk satu percobaan eksekusi'
        :!authenticated?'Autentikasi dan audit keputusan diperlukan'
        :executionReady?'Siap diperiksa ulang oleh backend'
        :activeDecision?.decision==='PASS'&&!planMatches?'PASS tersimpan tetapi tidak cocok dengan versi rencana sekarang'
        :activeDecision?.decision==='PASS'&&expired?'PASS kedaluwarsa (>60 menit); tinjau ulang'
        :activeDecision?`Keputusan terakhir: ${activeDecision.decision}`:'Belum ada keputusan PASS',
      why:executionReady?'Backend akan memeriksa ulang bukti, keputusan dan rencana sebelum menulis.'
        :'Eksekusi hanya berjalan setelah PASS manusia yang cocok dengan rencana saat ini dan belum kedaluwarsa.'},
  ];

  const next=!authenticated
    ?{label:'Isi token operator di Developer Console →',to:'/console',enabled:true,why:'Tanpa token, keputusan tidak dapat disimpan dan History tidak terbaca.'}
    :context?.completed
    ?{label:'Lihat hasil dan riwayat',to:'/verification',enabled:true,why:'Pekerjaan sudah selesai. Periksa hasil yang tersimpan sebelum menyiapkan pekerjaan baru.'}
    :!planReady
    ?{label:'Periksa rencana yang menghambat →',to:'/review-execute',enabled:true,why:'Rencana belum lolos pemeriksaan backend; periksa alasannya di halaman Review & Execute.'}
    :!evidenceValid
    ?{label:'Lihat kriteria yang belum valid →',to:'/review-execute',enabled:true,why:'PASS terkunci sampai semua kriteria tervalidasi.'}
    :!activeDecision
    ?{label:'Buka Review & Keputusan →',to:'/review-execute',enabled:true,why:'Bukti valid, rencana siap dan operator terautentikasi: keputusan PASS/FAIL/HOLD dapat dicatat.'}
    :{label:'Buka History & tindakan →',to:'/review-execute',enabled:true,why:'Keputusan sudah tercatat; periksa kesiapan eksekusi dan History.'};

  return {evidenceValid,planReady,operatorAuthenticated:authenticated,decisionAvailable,executionReady,
    activeDecision,staleDecision,checks,next};
}
