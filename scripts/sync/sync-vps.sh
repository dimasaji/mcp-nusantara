#!/usr/bin/env bash
set -euo pipefail

repo="$(git rev-parse --show-toplevel 2>/dev/null || true)"
remote="origin"
branch=""
dry_run=0

usage() {
  printf 'usage: sync-vps.sh [--repo PATH] [--remote NAME] [--branch NAME] [--dry-run]\n'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) repo="$2"; shift 2 ;;
    --remote) remote="$2"; shift 2 ;;
    --branch) branch="$2"; shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; usage >&2; exit 64 ;;
  esac
done

[ -n "$repo" ] || { printf 'not inside a git work tree\n' >&2; exit 2; }
[ -d "$repo" ] || { printf 'repo path does not exist: %s\n' "$repo" >&2; exit 2; }

git_dir="$(git -C "$repo" rev-parse --git-dir 2>/dev/null || true)"
[ -n "$git_dir" ] || { printf 'not a git repository: %s\n' "$repo" >&2; exit 2; }

current_branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
[ -n "$branch" ] || branch="$current_branch"
[ "$branch" != "HEAD" ] || { printf 'detached HEAD is not supported\n' >&2; exit 2; }

remote_url="$(git -C "$repo" remote get-url "$remote" 2>/dev/null || true)"
[ -n "$remote_url" ] || { printf 'remote not configured: %s\n' "$remote" >&2; exit 2; }
case "$remote_url" in
  *dimasaji/mcp-nusantara*) ;;
  *) printf 'unexpected remote URL: %s\n' "$remote_url" >&2; exit 2 ;;
esac

if [ -n "$(git -C "$repo" status --porcelain)" ]; then
  printf 'working tree is not clean\n' >&2
  exit 2
fi

before="$(git -C "$repo" rev-parse HEAD)"

if [ "$dry_run" -eq 1 ]; then
  printf 'DRY-RUN repo=%s remote=%s branch=%s before=%s\n' "$repo" "$remote" "$branch" "$before"
  exit 0
fi

if ! git -C "$repo" fetch "$remote" --prune; then
  printf 'fetch failed\n' >&2
  exit 5
fi

remote_ref="$remote/$branch"
if ! git -C "$repo" rev-parse --verify --quiet "refs/remotes/$remote_ref" >/dev/null; then
  printf 'remote branch not found: %s\n' "$remote_ref" >&2
  exit 2
fi

remote_commit="$(git -C "$repo" rev-parse "$remote_ref")"

if [ "$before" = "$remote_commit" ]; then
  printf 'SYNCED repo=%s branch=%s commit=%s\n' "$repo" "$branch" "$before"
  exit 0
fi

if git -C "$repo" merge-base --is-ancestor "$before" "$remote_commit"; then
  if ! git -C "$repo" merge --ff-only "$remote_commit"; then
    printf 'fast-forward failed\n' >&2
    exit 6
  fi
  after="$(git -C "$repo" rev-parse HEAD)"
  printf 'FAST-FORWARD branch=%s before=%s after=%s\n' "$branch" "$before" "$after"
  exit 0
fi

if git -C "$repo" merge-base --is-ancestor "$remote_commit" "$before"; then
  printf 'LOCAL_AHEAD branch=%s local=%s remote=%s push requires approval\n' "$branch" "$before" "$remote_commit" >&2
  exit 3
fi

printf 'DIVERGED branch=%s local=%s remote=%s manual reconciliation required\n' "$branch" "$before" "$remote_commit" >&2
exit 4
