#!/bin/sh
# sync-update.sh — Nusantara V1 controlled sync update
# Per contract Phase 13:
#   - Require clean working tree
#   - Require approved canonical branch
#   - Require no divergence
#   - Perform fast-forward only
#   - Validate dependency changes
#   - Run smoke tests
#   - Report result
#   - MUST NOT: force push, reset hard, delete data, upload secrets,
#     auto-merge when diverged, auto-deploy production
set -eu

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
if [ -z "$REPO_ROOT" ]; then
  echo "ERROR: not inside a git repository"
  exit 1
fi

cd "$REPO_ROOT"

CANONICAL_BRANCH="${SYNC_CANONICAL_BRANCH:-origin/codex/fullroot-control-20261007}"
APPROVED="${SYNC_APPROVED:-0}"

echo "=== NUSANTARA V1 SYNC UPDATE ==="
echo "Repository: $REPO_ROOT"
echo "Canonical branch: $CANONICAL_BRANCH"
echo ""

# 1. Require clean working tree
echo "--- Precondition: clean working tree ---"
if [ -n "$(git status --short)" ]; then
  echo "BLOCKED: working tree is dirty. Commit or stash changes first."
  git status --short
  exit 1
fi
echo "OK: working tree clean"

# 2. Require approved canonical branch
echo "--- Precondition: canonical branch approved ---"
if [ "$APPROVED" != "1" ]; then
  echo "BLOCKED: SYNC_APPROVED=1 not set. Canonical branch merge requires repository owner approval."
  echo "Set SYNC_APPROVED=1 only after owner confirms canonical branch."
  exit 1
fi
echo "OK: canonical branch approved"

# 3. Require no divergence
echo "--- Precondition: no divergence ---"
git fetch origin
DIV="$(git rev-list --left-right --count "HEAD...$CANONICAL_BRANCH" 2>/dev/null || echo "0 0")"
AHEAD="$(echo "$DIV" | cut -f1)"
BEHIND="$(echo "$DIV" | cut -f2)"
echo "Ahead: $AHEAD, Behind: $BEHIND"
if [ "$AHEAD" != "0" ] || [ "$BEHIND" != "0" ]; then
  echo "BLOCKED: divergence detected (ahead=$AHEAD behind=$BEHIND). Resolve via reconciliation branch + PR, not fast-forward."
  exit 1
fi
echo "OK: no divergence"

# 4. Perform fast-forward only
echo "--- Sync: fast-forward only ---"
CURRENT_BRANCH="$(git branch --show-current)"
echo "Current branch: $CURRENT_BRANCH"
git pull --ff-only origin "$CANONICAL_BRANCH"
echo "OK: fast-forward complete"

# 5. Validate dependency changes
echo "--- Validate: dependency changes ---"
if git diff --name-only HEAD@{1} HEAD 2>/dev/null | grep -qE 'requirements-lock\.txt|pyproject\.toml|frontend/package-lock\.json|frontend/package\.json'; then
  echo "NOTICE: dependency manifest changed. Review before installing."
  echo "Do NOT copy virtualenv or node_modules between environments."
  echo "Install from manifest/lockfile on each environment separately."
else
  echo "OK: no dependency manifest changes"
fi

# 6. Run smoke tests
echo "--- Smoke tests ---"
if [ -f tests/test_v1_smoke.py ] && [ -x .venv/bin/python ]; then
  .venv/bin/python -m pytest tests/test_v1_smoke.py -q || echo "WARNING: smoke tests failed"
else
  echo "SKIP: tests/test_v1_smoke.py or .venv not found"
fi

echo ""
echo "=== SYNC UPDATE COMPLETE ==="
echo "New HEAD: $(git rev-parse HEAD)"
