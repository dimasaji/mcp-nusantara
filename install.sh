#!/usr/bin/env bash
# ==============================================================================
# Nusantara V1 — Install Script (Linux / Windows via Git Bash / WSL)
# Menginstal dependensi dan menyiapkan basis pengetahuan dari PDF asli DAFDUK-01.
# ==============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "============================================================"
echo " Nusantara V1 — Instalasi Dependensi"
echo "============================================================"

# --- Python venv ---
if [ ! -d .venv-nusantara ]; then
  echo "[INFO] Membuat virtual environment Python..."
  python3 -m venv .venv-nusantara
fi
source .venv-nusantara/bin/activate
echo "[INFO] Menginstal paket Python backend..."
pip install --quiet --upgrade pip >/dev/null 2>&1 || true
pip install --quiet fastapi uvicorn pydantic >/dev/null
echo "[OK] Python backend siap."

# --- Ollama ---
if ! command -v ollama >/dev/null 2>&1; then
  echo "[INFO] Menginstal Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh || echo "[WARN] Gagal menginstal Ollama otomatis; pasang secara manual dari https://ollama.com"
fi
if command -v ollama >/dev/null 2>&1; then
  if ! pgrep -x ollama >/dev/null 2>&1; then
    nohup ollama serve >/tmp/nusantara-ollama.log 2>&1 &
    sleep 3
  fi
  echo "[INFO] Memuat model ${OLLAMA_MODEL:-llama3.2:1b}..."
  ollama pull "${OLLAMA_MODEL:-llama3.2:1b}" || echo "[WARN] Gagal pull model (pastikan jaringan tersedia)."
fi

# --- Frontend ---
FRONTEND_DIR="${ROOT}/frontend"
if [ -d "${FRONTEND_DIR}" ]; then
  echo "[INFO] Menginstal dependensi frontend (npm)..."
  (cd "${FRONTEND_DIR}" && npm install --quiet --no-audit --no-fund)
  echo "[OK] Frontend siap."
fi

# --- Environment ---
if [ ! -f .env ]; then
  cp .env.example .env
fi

echo ""
echo "============================================================"
echo " Instalasi selesai."
echo " Jalankan: ./start-linux.sh   (Linux)"
echo "           start-windows.bat  (Windows)"
echo "============================================================"
