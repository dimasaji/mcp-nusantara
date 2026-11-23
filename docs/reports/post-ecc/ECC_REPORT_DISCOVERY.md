# ECC Report Discovery

Contract: `NUS-V1-POST-ECC-001`

Date: 2026-11-22

Repository: `git@github-nusantara:dimasaji/mcp-nusantara.git`

Branch: `codex/ecc-fullstack-verification-20261122`

HEAD: `35efdd382405442a3aabe0e05b112f47a2ff3603`

## 1. Read-only repository baseline

Commands executed from `/data/home/mcp-nusantara`:

```bash
pwd
git status --short
git branch --show-current
git rev-parse HEAD
git remote -v
```

Observed:

```text
/data/home/mcp-nusantara
?? mcp-nusantara/
codex/ecc-fullstack-verification-20261122
35efdd382405442a3aabe0e05b112f47a2ff3603
origin git@github-nusantara:dimasaji/mcp-nusantara.git (fetch)
origin git@github-nusantara:dimasaji/mcp-nusantara.git (push)
```

`mcp-nusantara/` is an untracked duplicate checkout and was not used, staged, or modified.

## 2. File discovery

Command:

```bash
find . -type f \( \
  -iname '*ecc*report*.md' -o \
  -iname '*ecc*.json' -o \
  -iname '*ecc*.log' \
\) -not -path './.git/*'
```

Relevant result:

```text
./NUSANTARA_V1_ECC_FINAL_REPORT.md
./ECC_POST_VERIFICATION_REPORT.md
```

Other matches were false positives from chat-history IDs containing `ecc` substrings. `ECC_POST_VERIFICATION_REPORT.md` is a derived post-verification report created after the ECC report; it is not the originating ECC final report.

## 3. Git history discovery

Command requested by the contract:

```bash
git log --all --name-only --format='' |
  grep -i 'ecc' | sort -u
```

The raw command produced many false positives because SHA-256 hashes and fixture names contain `ecc`. A narrowed path search was therefore run:

```bash
git log --all --name-only --format='' | grep -iE '(ecc.*report|report.*ecc).*\.md$' | sort -u
git rev-list --objects --all | grep -iE '(ecc.*report|report.*ecc).*\.md$' | sort -u
```

Relevant historical paths:

```text
NUSANTARA_V1_ECC_FINAL_REPORT.md
ECC_POST_VERIFICATION_REPORT.md
```

No case-variant path `Nusantar_v1_ECC_FINAL_REPORT.MD` was found in the working tree or Git object history.

## 4. Authenticated report source

The requested report is present as a tracked file, not only as a loose blob.

```bash
git log --all --oneline --follow -- NUSANTARA_V1_ECC_FINAL_REPORT.md
git rev-parse HEAD:NUSANTARA_V1_ECC_FINAL_REPORT.md
git cat-file -t <resolved_sha>
git cat-file -p <resolved_sha> | wc -l
sha256sum NUSANTARA_V1_ECC_FINAL_REPORT.md
wc -l -c NUSANTARA_V1_ECC_FINAL_REPORT.md
```

Resolved values:

| Field | Value |
|---|---|
| Working-tree path | `NUSANTARA_V1_ECC_FINAL_REPORT.md` |
| Introducing commit | `7694446b85e3c71863815ddf983959eb4f161b37` |
| Commit subject | `fix: align RAG constants and record ECC verification` |
| Git blob SHA | `8d1049dc636d0f0d183e1bacbf1ef10c3347c9c2` |
| Object type | `blob` |
| File SHA-256 | `09fed37b951f9e8929e697f4b159ab7a10fc7fdf5b21e7dfb20773c8d2820ad1` |
| Size | 16,205 bytes |
| Lines | 246 |
| ECC baseline commit recorded in report | `8b7f9b78105bb3dc8bdc23c6a58d19716eea711b` |
| ECC baseline branch recorded in report | `codex/ecc-fullstack-verification-20261122` |

`git cat-file -p` confirmed that the blob content matches the report read for this contract. The report itself records these provenance fields at lines 3–7:

- Date: `2026-11-22`
- Commit baseline: `8b7f9b78105bb3dc8bdc23c6a58d19716eea711b`
- Branch: `codex/ecc-fullstack-verification-20261122`
- Working tree at audit time: `M app/knowledge/rag.py`, untracked `mcp-nusantara/` untouched
- Commit/push at audit time: `TIDAK dilakukan`

## 5. Source authentication status

`AUTHENTICATED_TRACKED_REPORT`

Rationale:

- The report is tracked in the current branch.
- Its Git blob resolves and is a valid blob.
- Current file SHA-256 and blob content were verified.
- Its internal provenance matches the branch and audit baseline commit known from repository history.

`REPORT_NOT_FOUND` does not apply.

## 6. Evidence files

- `/data/tmp/opencode/post_ecc_full_pytest.txt`
- `/data/tmp/opencode/post_ecc_targeted_rag.txt`
- `/data/tmp/opencode/post_ecc_rag_suite.txt`
- `/data/tmp/opencode/post_ecc_frontend_test.txt`
- `/data/tmp/opencode/post_ecc_frontend_build.txt`
- `/data/tmp/opencode/post_ecc_runtime_status.txt`
- `/data/tmp/opencode/post_ecc_python_env.txt`
