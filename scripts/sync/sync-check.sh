#!/bin/sh
# sync-check.sh — Nusantara V1 sync status check (read-only)
# Per contract Phase 13: no force push, no reset hard, no delete, no secrets upload,
# no auto-merge when diverged, no production auto-deploy.
set -eu

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
if [ -z "$REPO_ROOT" ]; then
  echo "ERROR: not inside a git repository"
  exit 1
fi

cd "$REPO_ROOT"

CANONICAL_BRANCH="${SYNC_CANONICAL_BRANCH:-origin/codex/fullroot-control-20261007}"

echo "=== NUSANTARA V1 SYNC CHECK ==="
echo "Repository: $REPO_ROOT"
echo "Host: $(hostname 2>/dev/null || unknown)"
echo ""

echo "--- Git state ---"
CURRENT_BRANCH="$(git branch --show-current)"
HEAD_SHA="$(git rev-parse HEAD)"
echo "Current branch: $CURRENT_BRANCH"
echo "HEAD SHA: $HEAD_SHA"
echo "Canonical branch: $CANONICAL_BRANCH"

CANONICAL_SHA="$(git rev-parse "$CANONICAL_BRANCH" 2>/dev/null || echo "NOT FOUND")"
echo "Canonical SHA: $CANONICAL_SHA"

echo ""
echo "--- Working tree ---"
git status --short
if [ -z "$(git status --short)" ]; then
  echo "Working tree: CLEAN"
else
  echo "Working tree: DIRTY (uncommitted changes above)"
fi

echo ""
echo "--- Remote fetch ---"
git fetch origin 2>/dev/null || echo "WARNING: fetch failed (check network/remote)"

echo ""
echo "--- Divergence vs canonical ---"
if [ "$CANONICAL_SHA" = "NOT FOUND" ]; then
  echo "Cannot compute divergence: canonical branch not found locally"
else
  DIV="$(git rev-list --left-right --count "HEAD...$CANONICAL_BRANCH" 2>/dev/null || echo "0 0")"
  AHEAD="$(echo "$DIV" | cut -f1)"
  BEHIND="$(echo "$DIV" | cut -f2)"
  echo "Ahead of canonical: $AHEAD"
  echo "Behind canonical: $BEHIND"
  if [ "$AHEAD" = "0" ] && [ "$BEHIND" = "0" ]; then
    echo "Status: SYNCHRONIZED"
  elif [ "$AHEAD" = "0" ]; then
    echo "Status: LOCAL BEHIND"
  elif [ "$BEHIND" = "0" ]; then
    echo "Status: LOCAL AHEAD"
  else
    echo "Status: DIVERGED"
  fi
fi

echo ""
echo "=== SYNC CHECK COMPLETE ==="
