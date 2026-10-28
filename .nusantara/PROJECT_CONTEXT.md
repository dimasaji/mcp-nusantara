# NUSANTARA AI - LOCAL PROJECT CONTEXT

## Project

Nusantara Core + Hermes

Root:

C:\Users\dmaza\mcp-starter

## Runtime

FastAPI:
http://127.0.0.1:8000

Ollama:
http://127.0.0.1:11434

Default local model:

llama3.2:1b

## Architecture

User
â†“
Language Engine
â†“
Problem Engine
â†“
Knowledge Engine
â†“
Deterministic Safety / Routing
â†“
Grounding Guard
â†“
Hermes / Ollama
â†“
Response

## Knowledge Engine

Legacy knowledge database:

data/knowledge/nusantara_knowledge.db

Production knowledge database:

data/knowledge/production_knowledge.db

Production modules:

app/knowledge/production_kb.py
app/knowledge/production_embedding_bridge.py

## Production Knowledge Roadmap

19.0 Production Knowledge Base
19.1 IndoBERT Embedding Bridge
19.2 Production Semantic Retriever
19.3 Production Hybrid RAG Bridge
19.4 Official Knowledge Ingestion
19.5 Production Grounding Benchmark
19.6 /v1/chat Integration
19.7 Full Regression
20.0 Production Knowledge Engine

## Safety Rules

Do NOT blindly modify:

app/api/routes.py
app/knowledge/rag.py

Always:

1. Read current source.
2. Backup before destructive change.
3. Use targeted patch.
4. Compile.
5. Run regression.
6. Preserve existing passing tests.

## Current Baseline

Compile:
PASS

Health:
PASS

API Contract:
20/20 PASS

E2E:
4/4 PASS

Production KB:
PASS

IndoBERT Bridge:
PASS

## Local-first principle

Prefer:

Python
FastAPI
Ollama
IndoBERT
SQLite
FTS5
Local embeddings
Graphify

Avoid unnecessary paid APIs.

## Developer instruction

Understand existing architecture before changing source.

Do not rewrite working modules unnecessarily.

Use isolated tests before production integration.
