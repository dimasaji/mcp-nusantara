#!/usr/bin/env bash
# ==============================================================================
# Nusantara V1 — Startup Script (Linux / Instabox 2 / PC Linux)
# Menjalankan backend Lean Intelligence Engine + frontend dev server di localhost.
# Tidak menggunakan Tailscale / Cloudflare. Tidak dibuka ke publik.
# ==============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# --- Environment ---
if [ ! -f .env ]; then
  cp .env.example .env
  echo "[INFO] .env dibuat dari .env.example (sesuaikan jika perlu)."
fi
set -a
. ./.env
set +a

export NUSANTARA_HOST="${NUSANTARA_HOST:-127.0.0.1}"
export NUSANTARA_PORT="${NUSANTARA_PORT:-8021}"
export OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2:1b}"

VENV="${ROOT}/.venv-nusantara"

echo "============================================================"
echo " Nusantara V1 — Lean Intelligence Engine (Linux)"
echo "============================================================"
echo "Backend : http://${NUSANTARA_HOST}:${NUSANTARA_PORT}"
echo "Knowledge DB: ${NUSANTARA_KNOWLEDGE_DB:-./data/knowledge/production_knowledge.db}"
echo "Ollama  : ${OLLAMA_URL} / ${OLLAMA_MODEL}"
echo "============================================================"

# --- Ollama (pastikan tersedia) ---
if ! command -v ollama >/dev/null 2>&1; then
  echo "[WARN] Ollama tidak ditemukan. LLM lokal tidak tersedia; backend tetap jalan (faktual struktur)."
else
  if ! pgrep -x ollama >/dev/null 2>&1; then
    echo "[INFO] Menyalakan Ollama..."
    nohup ollama serve >/tmp/nusantara-ollama.log 2>&1 &
    sleep 3
  fi
  if ! curl -s "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
    echo "[WARN] Ollama belum siap di ${OLLAMA_URL}."
  else
    echo "[OK] Ollama siap."
  fi
fi

# --- Backend (Python venv) ---
if [ -d "${VENV}" ]; then
  source "${VENV}/bin/activate"
else
  echo "[WARN] Virtual environment ${VENV} tidak ditemukan. Gunakan install.sh terlebih dahulu."
fi

echo "[INFO] Menyalakan backend di port ${NUSANTARA_PORT}..."
nohup python3 "${ROOT}/lia_engine.py" >/tmp/nusantara-backend.log 2>&1 &
BACKEND_PID=$!
sleep 3

if curl -s "http://${NUSANTARA_HOST}:${NUSANTARA_PORT}/v1/health" >/dev/null 2>&1; then
  echo "[OK] Backend siap di http://${NUSANTARA_HOST}:${NUSANTARA_PORT}/v1/health"
else
  echo "[ERROR] Backend gagal menyala. Lihat /tmp/nusantara-backend.log"
  exit 1
fi

# --- Frontend (React + Vite) ---
FRONTEND_DIR="${ROOT}/frontend"
if [ -d "${FRONTEND_DIR}/node_modules" ]; then
  echo "[INFO] Menyalakan frontend dev server (port 5173)..."
  (cd "${FRONTEND_DIR}" && nohup npm run dev >/tmp/nusantara-frontend.log 2>&1 &)
  echo "[OK] Frontend: http://localhost:5173 (proxy ke backend via NUSANTARA_BACKEND_URL)"
else
  echo "[WARN] Frontend node_modules tidak ditemukan. Jalankan install.sh, lalu 'cd frontend && npm run dev'."
  echo "       Atau build: cd frontend && npm run build  (hasil di dist/)"
fi

echo ""
echo "Semua layanan berjalan di localhost (tidak dibuka ke publik)."
echo "Log: /tmp/nusantara-backend.log, /tmp/nusantara-frontend.log, /tmp/nusantara-ollama.log"
echo "PID backend: ${BACKEND_PID}"
