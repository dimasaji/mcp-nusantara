$ErrorActionPreference="Stop"
$root=(Get-Location).Path
$ts=Get-Date -Format "yyyyMMdd_HHmmss"
$backup="$root\backup\rag_cache_$ts"
New-Item -ItemType Directory -Force "$root\config","$root\app\runtime","$root\scripts",$backup | Out-Null

@"
{
  "rag": {
    "enabled": true,
    "semantic_enabled": true,
    "lexical_enabled": true,
    "semantic_weight": 0.70,
    "lexical_weight": 0.30,
    "top_k": 5,
    "min_score": 0.35,
    "model": {
      "name": "indobenchmark/indobert-base-p1",
      "device": "cpu",
      "load_once": true,
      "singleton": true,
      "cache_model": true,
      "cache_tokenizer": true,
      "keep_in_memory": true
    },
    "performance": {
      "torch_threads": 4,
      "torch_interop_threads": 1,
      "max_sequence_length": 256,
      "batch_size": 1
    },
    "retrieval": {
      "use_sqlite_fts5": true,
      "use_embeddings": true,
      "rerank": true
    },
    "grounding": {
      "enabled": true,
      "evidence_first": true,
      "allow_model_only_answer": false,
      "max_evidence": 5
    }
  }
}
"@ | Set-Content "$root\config\rag_runtime.json" -Encoding UTF8

@"
import threading

_LOCK = threading.RLock()
_CACHE = {}

def get_cached(cls, *args, **kwargs):
    key = (
        cls.__module__,
        cls.__name__,
        repr(args),
        repr(sorted((k, str(v)) for k, v in kwargs.items()))
    )
    with _LOCK:
        if key not in _CACHE:
            _CACHE[key] = cls.from_pretrained(*args, **kwargs)
        return _CACHE[key]

def cache_stats():
    with _LOCK:
        return {
            "cached_objects": len(_CACHE),
            "keys": [f"{k[0]}.{k[1]}" for k in _CACHE]
        }

def clear_cache():
    with _LOCK:
        _CACHE.clear()
"@ | Set-Content "$root\app\runtime\indobert_cache.py" -Encoding UTF8

$targets=Get-ChildItem "$root\app" -Recurse -File -Filter "*.py" |
Where-Object { $_.FullName -notmatch "indobert_cache\.py$" }

$changed=0

foreach($f in $targets) {
    $s=Get-Content $f.FullName -Raw

    if($s -match "from_pretrained") {
        Copy-Item $f.FullName "$backup\$($f.Name).bak" -Force

        if($s -notmatch "app\.runtime\.indobert_cache") {
            $s="from app.runtime.indobert_cache import get_cached`r`n"+$s
        }

        $s=$s -replace "AutoModel\.from_pretrained\(", "get_cached(AutoModel,"
        $s=$s -replace "BertModel\.from_pretrained\(", "get_cached(BertModel,"
        $s=$s -replace "AutoTokenizer\.from_pretrained\(", "get_cached(AutoTokenizer,"
        $s=$s -replace "BertTokenizer\.from_pretrained\(", "get_cached(BertTokenizer,"
        $s=$s -replace "AutoConfig\.from_pretrained\(", "get_cached(AutoConfig,"

        Set-Content $f.FullName $s -Encoding UTF8
        $changed++
    }
}

@"
import json
import time
from pathlib import Path

print("="*70)
print("NUSANTARA RAG CACHE BASELINE")
print("="*70)

cfg=Path("config/rag_runtime.json")
print("CONFIG :",cfg.resolve())
print("EXISTS :",cfg.exists())

import torch
torch.set_num_threads(4)

try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

print("TORCH THREADS:",torch.get_num_threads())

from app.runtime.indobert_cache import get_cached,cache_stats
from transformers import AutoTokenizer,AutoModel

name="indobenchmark/indobert-base-p1"

print()
print("--- SINGLETON TEST ---")

t=time.perf_counter()
tok1=get_cached(AutoTokenizer,name)
model1=get_cached(AutoModel,name)
first=time.perf_counter()-t

t=time.perf_counter()
tok2=get_cached(AutoTokenizer,name)
model2=get_cached(AutoModel,name)
second=time.perf_counter()-t

print("FIRST LOAD :",round(first,3),"s")
print("SECOND LOAD:",round(second,3),"s")
print("TOKENIZER SAME:",tok1 is tok2)
print("MODEL SAME    :",model1 is model2)
print("CACHE:",json.dumps(cache_stats(),indent=2))

if tok1 is tok2 and model1 is model2 {
    print("RESULT: PASS - IndoBERT singleton/cache aktif.")
} else {
    print("RESULT: FAIL - cache belum aktif.")
}

print()
print("--- RETRIEVER IMPORT ---")

try:
    from app.knowledge.production_semantic_retriever import ProductionSemanticRetriever
    print("ProductionSemanticRetriever: IMPORT OK")
except Exception as e:
    print("ProductionSemanticRetriever: IMPORT ERROR")
    print(type(e).__name__,str(e))

print()
print("DONE")
"@ | Set-Content "$root\scripts\baseline_rag_cache.py" -Encoding UTF8

Write-Host ""
Write-Host "=== NUSANTARA RAG CACHE PATCH ===" -ForegroundColor Green
Write-Host "Changed files: $changed"
Write-Host "Backup: $backup"
Write-Host ""

python "$root\scripts\baseline_rag_cache.py"
