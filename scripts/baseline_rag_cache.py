import sys
import json
import time
from pathlib import Path

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 70)
print("NUSANTARA RAG CACHE BASELINE")
print("=" * 70)

# ============================================================
# CONFIG
# ============================================================

cfg = PROJECT_ROOT / "config" / "rag_runtime.json"

print("PROJECT ROOT:", PROJECT_ROOT)
print("CONFIG     :", cfg)
print("EXISTS     :", cfg.exists())

# ============================================================
# TORCH
# ============================================================

import torch

torch.set_num_threads(4)

try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

print("TORCH THREADS:", torch.get_num_threads())

# ============================================================
# CACHE
# ============================================================

from app.runtime.indobert_cache import get_cached, cache_stats
from transformers import AutoTokenizer, AutoModel

name = "indobenchmark/indobert-base-p1"

# ============================================================
# SINGLETON TEST
# ============================================================

print()
print("--- SINGLETON TEST ---")

t = time.perf_counter()

tok1 = get_cached(AutoTokenizer, name)
model1 = get_cached(AutoModel, name)

first = time.perf_counter() - t

t = time.perf_counter()

tok2 = get_cached(AutoTokenizer, name)
model2 = get_cached(AutoModel, name)

second = time.perf_counter() - t

print("FIRST LOAD :", round(first, 3), "s")
print("SECOND LOAD:", round(second, 3), "s")
print("TOKENIZER SAME:", tok1 is tok2)
print("MODEL SAME    :", model1 is model2)

print(
    "CACHE:",
    json.dumps(
        cache_stats(),
        indent=2,
        default=str,
    ),
)

# ============================================================
# RESULT
# ============================================================

if tok1 is tok2 and model1 is model2:
    print("RESULT: PASS - IndoBERT singleton/cache aktif.")
else:
    print("RESULT: FAIL - cache belum aktif.")

# ============================================================
# RETRIEVER IMPORT
# ============================================================

print()
print("--- RETRIEVER IMPORT ---")

try:
    from app.knowledge.production_semantic_retriever import ProductionSemanticRetriever
    print("ProductionSemanticRetriever: IMPORT OK")
except Exception as e:
    print("ProductionSemanticRetriever: IMPORT ERROR")
    print(type(e).__name__, str(e))

# ============================================================
# DONE
# ============================================================

print()
print("DONE")
