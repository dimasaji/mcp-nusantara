# Dependency Impact — LangChain & LangGraph

## Added Dependencies
- langchain 1.4.10
- langchain-core (transitive)
- langgraph (latest compatible)
- langchain-ollama (latest compatible)
- langsmith (transitive)
- langgraph-checkpoint (transitive)
- langgraph-prebuilt (transitive)
- langgraph-sdk (transitive)

## Installation
Packages installed in .venv via pip (copied from E:\AI\mcp-starter\.venv).

## Compatibility
- Python 3.13 ✅
- FastAPI ✅
- Existing dependencies ✅
- No conflicts detected

## Optional Dependency
Added to pyproject.toml:
```toml
[project.optional-dependencies]
langchain = ["langchain>=1.0", "langgraph>=0.2", "langchain-ollama>=0.2"]
```

## Feature Flags
- NUS_LANGCHAIN_ENABLED=false (default)
- NUS_LANGGRAPH_ENABLED=false (default)
PY