#!/usr/bin/env bash
set -uo pipefail
OUT=/data/workspace/nus-v1-vps-final-20261123/evidence
mkdir -p "$OUT"
run() {
  local name="$1"; shift
  local ts rc
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  set +e
  "$@" >"$OUT/${name}.out" 2>"$OUT/${name}.err"
  rc=$?
  set -e
  printf '%s\t%s\t%s\t%s\n' "$ts" "$name" "$rc" "$*" >>"$OUT/commands.tsv"
  printf '[%s] %s exit=%s\n' "$ts" "$name" "$rc"
}
