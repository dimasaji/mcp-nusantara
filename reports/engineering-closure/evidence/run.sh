EVIDENCE_DIR="${EVIDENCE_DIR:-reports/engineering-closure/evidence}"
mkdir -p "$EVIDENCE_DIR"
run() {
  name="$1"
  shift
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  "$@" >"$EVIDENCE_DIR/${name}.out" 2>"$EVIDENCE_DIR/${name}.err"
  rc=$?
  cmd_line=""
  for arg in "$@"; do
    cmd_line+="$(printf '%q' "$arg") "
  done
  cmd_line="${cmd_line% }"
  printf '%s\t%s\t%s\t%s\n' "$ts" "$name" "$rc" "$cmd_line" >>"$EVIDENCE_DIR/commands.tsv"
  printf '[%s] %s exit=%s\n' "$ts" "$name" "$rc"
  return $rc
}
