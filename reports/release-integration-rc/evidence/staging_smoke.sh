#!/usr/bin/env bash
set -uo pipefail
BASE=http://127.0.0.1:18214
TOKEN_FILE=/data/workspace/nus-v1-release-rc-20261123/evidence/staging.token
SESSION=web-11111111-2222-4333-8444-555555555555
fail=0
read -r TOKEN < "$TOKEN_FILE"

probe() {
  local name="$1"
  local expected="$2"
  local response
  local code=""
  shift 2
  printf '=== %s ===\n' "$name"
  response=$("$@" 2>&1)
  printf '%s\n' "$response"
  if [[ "$response" =~ HTTP[[:space:]]([0-9]+)$ ]]; then
    code=${BASH_REMATCH[1]}
  fi
  if [ "$code" != "$expected" ]; then
    printf 'EXPECTED_HTTP=%s ACTUAL_HTTP=%s\n' "$expected" "${code:-none}"
    fail=1
  fi
}

probe health 200 curl --noproxy '*' -sS --max-time 30 -w '\nHTTP %{http_code}' "$BASE/health"
probe readyz 200 curl --noproxy '*' -sS --max-time 30 -w '\nHTTP %{http_code}' "$BASE/readyz"
probe model_status 200 curl --noproxy '*' -sS --max-time 30 -w '\nHTTP %{http_code}' -H "X-Admin-Token: $TOKEN" "$BASE/v1/control-plane/model-status"
probe admin_negative 403 curl --noproxy '*' -sS --max-time 30 -w '\nHTTP %{http_code}' -X POST -H 'Content-Type: application/json' -H 'X-Admin-Token: invalid-release-rc-token' -d "{\"session_id\":\"$SESSION\",\"user_input\":\"PONG\"}" "$BASE/v1/chat"
probe ollama_chat 200 curl --noproxy '*' -sS --max-time 120 -w '\nHTTP %{http_code}' -X POST -H 'Content-Type: application/json' -H "X-Admin-Token: $TOKEN" -d "{\"session_id\":\"$SESSION\",\"user_input\":\"Balas tepat PONG\"}" "$BASE/v1/chat"
probe chat_history 200 curl --noproxy '*' -sS --max-time 30 -w '\nHTTP %{http_code}' -H "X-Admin-Token: $TOKEN" -H "X-Chat-Session: $SESSION" "$BASE/v1/chat/history"

exit "$fail"
