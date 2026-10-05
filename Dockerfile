FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic pydantic-settings python-dotenv httpx
RUN python -m venv /opt/indobert \
    && /opt/indobert/bin/pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && /opt/indobert/bin/pip install --no-cache-dir transformers
ENV NUSANTARA_INDOBERT_PYTHON=/opt/indobert/bin/python \
    NUSANTARA_INDOBERT_WORKER=/app/nusantara-models/indobert_worker.py \
    HF_HOME=/app/data/huggingface
COPY app ./app
COPY docs ./docs
COPY .env.example ./
COPY scripts/healthcheck.py ./scripts/healthcheck.py
COPY nusantara-models/indobert_worker.py ./nusantara-models/indobert_worker.py
RUN useradd -r -u 10001 appuser && mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python scripts/healthcheck.py
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
