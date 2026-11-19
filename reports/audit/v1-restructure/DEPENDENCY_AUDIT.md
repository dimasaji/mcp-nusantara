# DEPENDENCY_AUDIT

**Project:** Nusantara V1
**Contract:** deliverable §12.14, addendum §5.E
**Date:** 2026-11-18
**Method:** `pip list --format=freeze` inside `.venv`, `node -e` against `node_modules`, `npm audit`, and manual reconciliation of `pyproject.toml` against the installed set

---

## 1. Python dependencies

### 1.1 Declared vs installed — reconciliation

| Package | `pyproject.toml` declares | Installed | Verdict |
|---|---|---|---|
| `fastapi` | `>=0.115.0` | **0.141.1** | ✅ satisfied |
| `uvicorn[standard]` | `>=0.30.0` | **0.54.0** | ✅ satisfied |
| `pydantic` | `>=2.9.0` | **2.13.5** | ✅ satisfied |
| `pydantic-settings` | `>=2.5.0` | **2.15.0** | ✅ satisfied |
| `python-dotenv` | `>=1.0.0` | **1.2.3** | ✅ satisfied |
| `httpx` | `>=0.27.0` | **0.28.1** | ✅ satisfied |
| `haystack-ai` | **`==2.31.1`** | **3.4.1** | ❌ **VIOLATED — major version** |
| `pypdf` | `>=6.20,<7` | 6.20.1 | ✅ satisfied |
| `pymupdf` | `>=1.28,<2` | 1.28.2 | ✅ satisfied |
| `Pillow` | `>=10` | 12.3.0 | ✅ satisfied |
| `mcp` | `>=1.30,<2` | 1.30.0 | ✅ satisfied |
| `langgraph` (workflow extra) | **`==1.2.14`** | **1.2.20** | ❌ **VIOLATED — exact pin** |
| `langchain` | `>=1.4` | 1.4.10 | ✅ satisfied |
| `langchain-ollama` | `>=0.2` | 1.1.0 | ✅ satisfied |
| `pytest` | `>=8.3.0` | 9.1.1 | ✅ satisfied |
| `pytest-asyncio` | `>=0.23.0` | 1.4.0 | ✅ satisfied |
| `ruff` | `>=0.5.0` | 0.16.10 | ✅ satisfied |
| `mypy` | `>=1.10.0` | 2.4.0 | ✅ satisfied |

Installed package count: **101**.

### 1.2 D1 — `haystack-ai` pin is wrong by a major version (**HIGH**)

```toml
# pyproject.toml
dependencies = [
    …
    "haystack-ai==2.31.1",
]
```

Actual runtime: `haystack.__version__` → **`3.4.1`**.

Consequence: running `pip install -e .` or `pip install .` today would **downgrade Haystack from 3.4.1 to 2.31.1**, silently changing a core dependency of the knowledge pipeline. The application code was exercised against 3.4.1 by every test in this audit. The declared pin describes a state that does not exist.

This is the single most dangerous metadata defect found: it is latent, it activates on a routine command, and it would break the knowledge pipeline with no error at install time.

**Action:** correct the pin to the tested version. **Not applied** — changing a dependency constraint is a security/dependency change requiring approval.

### 1.3 D2 — `langgraph==1.2.14` is not installed (**MEDIUM**)

Two extras declare contradictory constraints:

```toml
workflow  = ["langgraph==1.2.14"]     # exact pin
langchain = ["langgraph>=0.2"]        # open range
```

Installed: **1.2.20**. The `workflow` extra cannot be installed as written without downgrading the running environment. Because `langchain` also pulls `langgraph>=0.2`, installing both extras together is unsatisfiable at `1.2.14`.

**Action:** drop the exact pin or align it to the tested version. Not applied.

### 1.4 D3 — no Python lock file (**MEDIUM**)

There is no `requirements.txt`, no `poetry.lock`, no `uv.lock`, no `pip-tools` output. `.gitignore` contains `*.lock`, which actively prevents one from being committed.

`requirements-docling.lock` (2,013 bytes) exists for the **Docling** environment only; it is not the application's lock.

Consequence: the 101-package environment is not reproducible. Two machines running `pip install -e .[dev,langchain,mcp]` on different days will get different builds. Every measurement in this audit is tied to the environment captured in §1.1, not to a reproducible specification.

**Action:** generate and commit a lock. Not applied — `.gitignore` deliberately ignores `*.lock`, so changing this is a policy decision.

### 1.5 D4 — no Python vulnerability scan (**NOT TESTED**)

`pip-audit` is not installed and no offline advisory database is available:

```
No module named pip_audit
```

**No claim is made about Python CVEs.** This is a measurement gap, not a clean result.

### 1.6 Direct dependency surface is small — and that is good

Only **7** direct runtime dependencies (fastapi, uvicorn, pydantic, pydantic-settings, python-dotenv, httpx, haystack-ai) plus four opt-in extras. The remaining ~94 installed packages are transitive.

Notable heavy transitives and why they exist:

| Package | Pulled in by | Note |
|---|---|---|
| `torch`, `transformers` | IndoBERT embedding bridge | separate venv in Docker (`/opt/indobert`) |
| `docling` stack | `requirements-docling.lock` | separate environment entirely |
| `langchain`, `langgraph` | `langchain` / `workflow` extras | optional |

Keeping torch/transformers out of the main environment is the right call — the Dockerfile puts them in `/opt/indobert` rather than the app venv, which is why the image is 2.48 GB rather than far larger.

---

## 2. Node dependencies

### 2.1 Runtime dependencies (6)

| Package | Declared | Installed |
|---|---|---|
| `react` | `^19.0.0` | **19.3.0** |
| `react-dom` | `^19.0.0` | **19.3.0** |
| `@tanstack/react-router` | `^1.0.0` | **1.170.41** |
| `@tanstack/react-query` | `^5.0.0` | **5.104.1** |
| `zod` | `^4.0.0` | **4.6.5** |
| `@xyflow/react` | `^12.0.0` | **12.12.0** |

### 2.2 Dev dependencies (12)

`typescript` 5.9.3 · `vite` 7.3.7 · `@vitejs/plugin-react` 5.2.0 · `vitest` 3.2.7 · `@testing-library/react` 16.3.3 · `@testing-library/jest-dom` 6.9.1 · `@playwright/test` 1.63.0 · `jsdom` 26.1.0 · `@types/react` 19.3.0 · `@types/react-dom` 19.3.0 · `@types/node` 22.20.5

All declared ranges are satisfied.

### 2.3 N1 — two known vulnerabilities (**1 high, 1 moderate**) — measured

`npm audit --omit=dev` was executed against the committed `package-lock.json`:

```
seroval  1.5.5 - 1.6.10
Severity: moderate
  Seroval: Code injection through a typed array's own constructor property
           GHSA-f86p-h4j2-7qgj
  Seroval: Script injection through RegExp sources in serialized output
           GHSA-9wx9-5pv9-3349
  fix available via `npm audit fix`
  node_modules/seroval

zod  <4.6.6
Severity: high
  Zod can exhaust memory while validating oversized constrained collections
  GHSA-mrhx-c7xc-m3w5
  fix available via `npm audit fix`
  node_modules/zod

2 vulnerabilities (1 moderate, 1 high)
```

**Detail on the high-severity finding:** `zod` is the request/response validator for every API call the frontend makes. The advisory is a denial-of-service (memory exhaustion on oversized constrained collections), not remote code execution. The frontend validates data it receives from its own backend, so exploitability is limited — but `zod` is also a **runtime** dependency and this is the only high-severity CVE anywhere in the dependency tree.

**Fix:** `npm audit fix` moves `zod` 4.6.5 → 4.6.6 and `seroval` to a patched release. Both are patch-level.

**Action: NOT APPLIED — requires approval.** Applying it changes `package-lock.json`, requires a `dist/` rebuild, and requires re-running the frontend suite. It is recorded here with the exact remediation command.

### 2.4 N2 — `seroval` is a transitive of `@tanstack/react-router`

`seroval` is not used directly; it is pulled in by TanStack Router for serialisation. Neither advisory is reachable in this application's code path (the app does not serialise typed arrays or RegExp sources into route state), but the dependency is still present in the shipped bundle.

---

## 3. Supply-chain controls

| Control | Status |
|---|---|
| `package-lock.json` committed | **YES** — 120,234 bytes |
| Python lock committed | **NO** — actively ignored |
| `.github/workflows` CI | **NO** — `.github` does not exist in the tree |
| Dependabot / Renovate | **NO** |
| `npm audit` in CI | **NO** |
| `pip-audit` in CI | **NO** |
| SBOM | **NO** |
| Image signing (cosign) | **NO** |
| Base image digest pinning | **NO** — `FROM python:3.12-slim` floats |
| `--no-cache-dir` in Docker pip install | **YES** |

### 3.1 Finding — the base image floats

```dockerfile
FROM python:3.12-slim
```

No digest. Two builds a month apart produce different images from the same `Dockerfile`. Combined with no Python lock, the container is **not reproducible** even though the source is fixed at commit `7867ba35`.

**Action:** pin by digest. Not applied.

---

## 4. Docker dependency footprint — measured

| Layer | Content | Effect on image |
|---|---|---|
| `python:3.12-slim` | base | ~130 MB |
| `pip install fastapi uvicorn pydantic … haystack-ai==2.31.1` | **hardcoded in `Dockerfile:5`, ignores `pyproject.toml`** | bulk |
| `/opt/indobert` venv | `torch` (CPU index) + `transformers` | **largest layer** |
| `COPY app`, `docs`, `control-plane/dist`, scripts | source + frontend | small |
| **Total image** | `nusantara:v1-dist` | **2.48 GB** |

### 4.1 Finding — `Dockerfile` re-declares dependencies instead of using `pyproject.toml`

```dockerfile
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic pydantic-settings \
    python-dotenv httpx haystack-ai==2.31.1
```

`pyproject.toml` is copied in, then **ignored**. The dependency list is duplicated by hand in the Dockerfile with its own (also wrong) Haystack pin. This is a second, independent source of dependency truth that can drift from the first — and already has.

**Action:** replace with `pip install .` or `pip install -r requirements.lock`. Not applied.

---

## 5. Findings summary

| # | Finding | Severity | Action |
|---|---|---|---|
| **D1** | `haystack-ai==2.31.1` declared, **3.4.1** installed — major drift | **HIGH** | Requires approval |
| **D2** | `langgraph==1.2.14` declared, **1.2.20** installed; contradictory constraints across extras | Medium | Requires approval |
| **D3** | No Python lock; `*.lock` gitignored | Medium | Requires approval |
| **D4** | Python vulnerabilities unscreened (`pip-audit` absent) | **NOT TESTED** | Tooling gap |
| **N1** | `zod < 4.6.6` **high** CVE + `seroval` moderate, 2 advisories | **HIGH** | `npm audit fix`, requires approval |
| **N2** | `seroval` transitive reachable only via router serialisation | Low | Follows N1 |
| **S1** | No CI, no Dependabot, no SBOM, no image signing | Medium | Not implemented |
| **S2** | Base image floats (`python:3.12-slim`, no digest) | Medium | Not implemented |
| **S3** | `Dockerfile` hardcodes deps and ignores `pyproject.toml` | **HIGH** | Not implemented |

---

## 6. Verdict

| Criterion | Result |
|---|---|
| Declared constraints match installed set | **FAIL** — 2 violations, one major |
| Python environment reproducible | **FAIL** — no lock |
| Node environment reproducible | **PASS** — `package-lock.json` committed |
| No known Python CVEs | **NOT TESTED** |
| No known Node CVEs | **FAIL** — 1 high, 1 moderate, patch fixes available |
| Dependency source of truth is single | **FAIL** — `pyproject.toml` + `Dockerfile` diverge |
| Direct dependency count is disciplined | **PASS** — 7 runtime + 6 frontend runtime |

**Dependency status: PARTIAL.** Nothing was upgraded or downgraded during this audit. Every defect above is recorded with the exact command that would fix it, and every fix is withheld because it changes the dependency graph.
