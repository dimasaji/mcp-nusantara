# MDA PHASE-0 → R1 AUTHORIZATION MASTER COMMAND

## Tujuan

Jalankan satu command PowerShell dari:

```text
C:\Users\dmaza\mcp-starter
```

untuk melakukan:

1. Membuat `MDA-CHATGPT-DEVELOPER-001`
2. Membuat `MDA-MASTER-R1-MDE10-001`
3. Menghitung SHA256 kedua kontrak
4. Membuat MASTER CONTRACT CHECKPOINT
5. Melakukan Master State Discovery
6. Melakukan R1 exact-scope hash gate
7. Tidak melakukan implementation
8. Tidak mengubah database
9. Tidak melakukan Git reset/clean/restore
10. Berhenti pada `READY_FOR_R1_AUTHORIZATION`
11. Menunggu approval manusia
12. Setelah approval eksplisit, R1 baru boleh dieksekusi sebagai phase terpisah

---

# MASTER COMMAND

**Jalankan dari root repository Nusantara:**

```powershell
$ErrorActionPreference='Stop'; Set-Location 'C:\Users\dmaza\mcp-starter'; $ts=Get-Date -Format 'yyyyMMdd_HHmmss'; $root=(Get-Location).Path; $cmdDir=Join-Path $root 'docs\commands'; $devDir=Join-Path $root '.dev'; New-Item -ItemType Directory -Force $cmdDir,$devDir | Out-Null; Write-Host "`n==================================================" -ForegroundColor Cyan; Write-Host " MDA PHASE-0 -> R1 AUTHORIZATION MASTER COMMAND" -ForegroundColor Cyan; Write-Host "==================================================" -ForegroundColor Cyan; Write-Host "Repository : $root"; Write-Host "Timestamp  : $ts"; Write-Host "MODE       : READ-ONLY GOVERNANCE / CONTRACT INSTALL"; Write-Host "R1         : NOT AUTHORIZED"; Write-Host ""

$contract1=@'
# MDA-CHATGPT-DEVELOPER-001
## MASTER DEVELOPER ENGINE — AI DEVELOPMENT GOVERNANCE CONTRACT

Role:
ChatGPT sebagai Master Developer Engine (MDA) untuk Nusantara Core + Hermes.

Operating Mode:
Evidence-Driven / Scope-Bound / Human-Gated.

Core Principle:
Evidence Before Change.

MDA responsibilities:
- architecture analysis
- source development
- testing
- verification
- audit
- documentation
- rollback planning
- checkpointing

Human responsibilities:
- final authorization
- risk acceptance
- production approval
- high-risk operation approval
- final acceptance

Authority:
LEVEL A = READ ONLY.
LEVEL B = CONTROLLED DEVELOPMENT setelah explicit scope authorization.
LEVEL C = HIGH RISK / PROTECTED dan selalu membutuhkan explicit human authorization.

Protected state:
- production database
- SQLite WAL/SHM
- production index
- credentials
- secrets
- deployment state
- runtime state

Forbidden without explicit authorization:
- git reset --hard
- git clean -fd
- git clean -fdx
- git restore .
- destructive cleanup
- production DB mutation
- WAL/SHM recreation
- production index rebuild
- model installation
- deployment
- production service activation
- security/approval bypass

Evidence states:
UNKNOWN
NOT_VERIFIED
NOT_RUN
PARTIAL
BLOCKED
VERIFIED
ACCEPTED

MDA must never fabricate:
- files
- hashes
- test results
- runtime state
- model identity
- database state
- deployment state
- authorization

MDA must preserve pre-existing workspace changes.

Every controlled change requires:
baseline
scope
implementation
test
verification
checkpoint
rollback boundary

Master rule:
ChatGPT is Master Developer Engine, not Master Authority.

Human remains final authority for authorization, risk acceptance, production change, and final acceptance.
'@

$contract2=@'
# MDA-MASTER-R1-MDE10-001
## NUSANTARA CORE + HERMES
### CONTROLLED DEVELOPMENT MASTER COMMAND

Role:
ChatGPT = Master Developer Engine (MDA).

Objective:
Safely guide Nusantara Core + Hermes from R1 through MDE10.

Execution chain:

R1 Effective Configuration
    ->
R2 Provider / Model Runtime Identity
    ->
R3 Effective RAG Profile
    ->
R4 Embedding / Index Compatibility
    ->
R5 Runtime Enforcement
    ->
R6 Capability / Governance
    ->
MDE10 Live Runtime Verification
    ->
Final Architecture Acceptance
    ->
V1 Readiness

Master workflow:

DISCOVER
PLAN
AUTHORIZE
BASELINE
IMPLEMENT
TEST
VERIFY
AUDIT
CHECKPOINT
REPORT

Never skip authorization.

Never infer authorization from:
- previous conversations
- proposal existence
- successful tests
- checkpoint existence
- recommendation
- repository state

R1:
Use exact scope defined by:
docs/MDA_R1_LOCAL_001_PROPOSAL.md

R1 objective:
Compose EffectiveConfiguration using existing configuration ownership and composition architecture without creating a duplicate configuration system.

R1 must preserve:
- configuration precedence
- explicit overrides
- request-level override semantics
- omitted top_k semantics
- layer attribution
- secret protection
- existing provider architecture
- existing KnowledgeEngine architecture

R2:
Prove provider identity, model identity, selected model, actual runtime model, health and fallback behavior.

R3:
Prove one effective RAG profile including canonical retrieval policy, embedding profile, relevance and grounding policy.

R4:
Prove embedding/index compatibility including model, dimension, chunk identity, index identity and knowledge database identity.

R5:
Prove actual runtime consumption of effective configuration, provider, model, RAG, embedding and index.

R6:
Prove capability registration, actor binding, authorization and governance.

MDE10:
Perform live runtime verification and prove:
- source build identity
- runtime build identity
- model identity
- configuration identity
- RAG identity
- embedding identity
- index identity
- dependency chain
- capability enforcement

MDE10 must not be executed before R1-R6 are verified and separately authorized.

Protected state remains read-only unless separately authorized.

No automatic:
- database repair
- WAL/SHM recreation
- production index rebuild
- model installation
- service deployment
- git reset
- git clean
- mass cleanup

Current starting state:
MDE09 = DONE_SCOPED_CLOSURE_WITH_HOLD
R1 = PLANNED / NOT_AUTHORIZED
R2 = NOT_STARTED
R3 = NOT_STARTED
R4 = NOT_STARTED
R5 = NOT_STARTED
R6 = NOT_STARTED
MDE10 = NOT_STARTED

First execution:
Perform contract installation, state discovery and R1 exact-scope verification only.

After exact R1 scope verification:
STOP.

Do not implement R1 until explicit human authorization is received.

Valid authorization example:
APPROVED: R1-LOCAL-001
SCOPE: exact proposal scope
OBJECTIVE: implement effective configuration composition
'@

$p1=Join-Path $cmdDir 'MDA-CHATGPT-DEVELOPER-001.md'; $p2=Join-Path $cmdDir 'MDA-MASTER-R1-MDE10-001.md'; Set-Content $p1 $contract1 -Encoding UTF8; Set-Content $p2 $contract2 -Encoding UTF8; $h1=(Get-FileHash $p1 -Algorithm SHA256).Hash.ToLower(); $h2=(Get-FileHash $p2 -Algorithm SHA256).Hash.ToLower(); Write-Host "CONTRACT 1 : $p1"; Write-Host "SHA256     : $h1"; Write-Host "CONTRACT 2 : $p2"; Write-Host "SHA256     : $h2"; Write-Host ""

$gitBranch=(git branch --show-current 2>$null); $gitHead=(git rev-parse HEAD 2>$null); $db='data\knowledge\nusantara_knowledge.db'; $dbExists=Test-Path $db; $dbHash=if($dbExists){(Get-FileHash $db -Algorithm SHA256).Hash.ToLower()}else{'MISSING'}; $wal=Test-Path ($db+'-wal'); $shm=Test-Path ($db+'-shm'); $mde09=Test-Path '.dev\MDE09_CHECKPOINT.json'; $mda=Test-Path '.dev\MDA_POST_MDE09_001_CHECKPOINT.json'; $r1proposal=Test-Path 'docs\MDA_R1_LOCAL_001_PROPOSAL.md'; $tracked=(git status --short 2>$null | Where-Object {$_ -match '^\s*[MARCDU?]'}).Count; $untracked=(git status --short 2>$null | Where-Object {$_ -match '^\s*\?\?' }).Count

$expected=@{
'app/core/nusantara_config.py'='3d18304750d9b43e6cf33a19f5f1d73ea5b05bf2b22d9686deecd6fd4371911d';
'app/core/config.py'='996bfaed79b989576ec31dd10f9d94f5bc419466dc67e4da5c54f7666e3af5b6';
'app/main.py'='40debcba1d369cc25838ae7ac46cb145a845d0e7170f3a25c016fb867e24743c';
'app/api/routes.py'='ee5eceefbc479eaf4426f2f8d97bde674a6a951b139dc861dcd5f6701339c8a4';
'app/api/v2_routes.py'='85548ab3f8573a0e5900e4f8650f499b7864782b16bc374f927a1589c62ca8a7';
'app/models/ollama.py'='73f4f268d655ee425b25b0a4b399bd4c503c773d1a7d5949831e2fbb34ad904b';
'app/knowledge/engine.py'='eb7836d0edf858303bbc14cce30cdfe007fd7f22fa9521489a71c2447c26a43b';
'tests/test_configuration_contract.py'='bc4478e0100bab03d2dc8580cbf6a8e29176b7fdbc690795a745a732551d7123';
'tests/test_configuration_integration.py'='2becf4883d6eccc9cd364c64a7b9be1638f5a8cd04136d8d4229e8399f2d680b';
'tests/test_model_router_configuration.py'='b0ce4e26bec018425b8965fefb616c2bb5f001cc7b7990d9c94064c744397f61'
}

$results=@(); foreach($f in $expected.Keys){if(Test-Path $f){$a=(Get-FileHash $f -Algorithm SHA256).Hash.ToLower();$e=$expected[$f];$s=if($a -eq $e){'MATCH'}else{'MISMATCH'};$results+=,[pscustomobject]@{File=$f;Status=$s;Expected=$e;Actual=$a}}else{$results+=,[pscustomobject]@{File=$f;Status='MISSING';Expected=$expected[$f];Actual=''}};}; $match=($results|Where-Object Status -eq 'MATCH').Count; $bad=$results.Count-$match

$checkpoint=[ordered]@{
checkpoint='MDA_MASTER_CONTRACT_CHECKPOINT'
timestamp=(Get-Date).ToUniversalTime().ToString('o')
repository=$root
branch=$gitBranch
head=$gitHead
contract_1=[ordered]@{path='docs/commands/MDA-CHATGPT-DEVELOPER-001.md';sha256=$h1}
contract_2=[ordered]@{path='docs/commands/MDA-MASTER-R1-MDE10-001.md';sha256=$h2}
protected_database=[ordered]@{path=$db;exists=$dbExists;sha256=$dbHash;wal_present=$wal;shm_present=$shm}
prior_evidence=[ordered]@{mde09_checkpoint=$mde09;mda_post_mde09_checkpoint=$mda;r1_proposal=$r1proposal}
r1_exact_scope=[ordered]@{files=$results;match=$match;mismatch_or_missing=$bad}
authorization=[ordered]@{r1='NOT_AUTHORIZED';database_write='FALSE';source_reset='FALSE';cleanup='FALSE';production='FALSE'}
status=if($bad -eq 0 -and $r1proposal -and $mde09 -and $mda){'READY_FOR_R1_AUTHORIZATION'}else{'BLOCKED'}
next_action=if($bad -eq 0 -and $r1proposal -and $mde09 -and $mda){'WAIT_FOR_EXPLICIT_HUMAN_R1_APPROVAL'}else{'RECONCILE_PRECONDITIONS'}
}; $cp=Join-Path $devDir 'MDA_MASTER_CONTRACT_CHECKPOINT.json'; $checkpoint|ConvertTo-Json -Depth 8|Set-Content $cp -Encoding UTF8

Write-Host "`n=== MASTER STATE DISCOVERY ===" -ForegroundColor Cyan; Write-Host "BRANCH                  : $gitBranch"; Write-Host "HEAD                    : $gitHead"; Write-Host "MDE09 CHECKPOINT        : $mde09"; Write-Host "MDA CHECKPOINT          : $mda"; Write-Host "R1 PROPOSAL             : $r1proposal"; Write-Host "DATABASE                : $dbExists"; Write-Host "DATABASE SHA256         : $dbHash"; Write-Host "WAL PRESENT             : $wal"; Write-Host "SHM PRESENT             : $shm"; Write-Host "TRACKED STATUS ENTRIES  : $tracked"; Write-Host "UNTRACKED STATUS ENTRIES: $untracked"; Write-Host ""

Write-Host "=== R1 EXACT-SCOPE HASH GATE ===" -ForegroundColor Cyan; $results|Format-Table -AutoSize; Write-Host "MATCH: $match"; Write-Host "MISMATCH_OR_MISSING: $bad"; Write-Host ""; Write-Host "R1_EXECUTION_AUTHORIZED : FALSE" -ForegroundColor Yellow; Write-Host "DATABASE_WRITE_AUTHORIZED: FALSE" -ForegroundColor Yellow; Write-Host "SOURCE_RESET_AUTHORIZED : FALSE" -ForegroundColor Yellow; Write-Host "CLEANUP_AUTHORIZED      : FALSE" -ForegroundColor Yellow; Write-Host ""

if($bad -eq 0 -and $r1proposal -and $mde09 -and $mda){Write-Host "==================================================" -ForegroundColor Green; Write-Host " READY_FOR_R1_AUTHORIZATION" -ForegroundColor Green; Write-Host "==================================================" -ForegroundColor Green; Write-Host "Checkpoint: $cp"; Write-Host ""; Write-Host "STOP: R1 BELUM DIIMPLEMENTASIKAN." -ForegroundColor Yellow; Write-Host "Menunggu explicit human approval."; Write-Host ""; Write-Host "Approval yang diperlukan:" -ForegroundColor Cyan; Write-Host "APPROVED: R1-LOCAL-001"; Write-Host "SCOPE: exact proposal scope"; Write-Host "OBJECTIVE: implement effective configuration composition"}else{Write-Host "==================================================" -ForegroundColor Red; Write-Host " BLOCKED — R1 CANNOT START" -ForegroundColor Red; Write-Host "==================================================" -ForegroundColor Red; Write-Host "Checkpoint: $cp"; Write-Host "Reconcile missing/mismatched preconditions before authorization."}
```

## Yang dilakukan command ini

```text
1. CREATE CONTRACTS
       ↓
2. SHA256 CONTRACTS
       ↓
3. READ CURRENT STATE
       ↓
4. CREATE MASTER CHECKPOINT
       ↓
5. VERIFY R1 PROPOSAL
       ↓
6. VERIFY 10 FILE HASH
       ↓
7. STOP
```

**Tidak ada R1 implementation di command ini.**

Bahkan jika semua gate PASS, hasil akhirnya hanya:

```text
READY_FOR_R1_AUTHORIZATION
```

lalu menunggu Anda memberikan:

```text
APPROVED: R1-LOCAL-001
SCOPE: exact proposal scope
OBJECTIVE: implement effective configuration composition
```

### Catatan penting

Command di atas **menulis dua file kontrak dan satu checkpoint**. Itu memang perubahan workspace, tetapi **bukan perubahan source Nusantara, database, runtime, atau production state**.

Setelah Anda menjalankan command tersebut, **kirim seluruh output PowerShell-nya ke sini**. Dari output itu saya akan menentukan apakah kita benar-benar berada pada `READY_FOR_R1_AUTHORIZATION` atau ada precondition yang masih `BLOCKED`.
