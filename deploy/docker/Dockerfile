FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml .
COPY deploy/docker/requirements.txt /tmp/requirements.txt
COPY deploy/docker/requirements-indobert.txt /tmp/requirements-indobert.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
ENV HAYSTACK_TELEMETRY_ENABLED=False
RUN python -m venv /opt/indobert \
    && /opt/indobert/bin/pip install --no-cache-dir torch==2.9.1+cpu --index-url https://download.pytorch.org/whl/cpu \
    && /opt/indobert/bin/pip install --no-cache-dir -r /tmp/requirements-indobert.txt
ENV NUSANTARA_INDOBERT_PYTHON=/opt/indobert/bin/python \
    NUSANTARA_INDOBERT_WORKER=/opt/indobert-worker/indobert_worker.py \
    HF_HOME=/app/data/huggingface
COPY backend/app ./app
COPY frontend/dist ./frontend/dist
COPY docs ./docs
COPY .env.example ./
COPY scripts/healthcheck.py ./scripts/healthcheck.py
RUN useradd -r -u 10001 appuser && mkdir -p /app/data /home/appuser && chown -R appuser:appuser /app /home/appuser
USER appuser
EXPOSE 18201
HEALTHCHECK --interval=30s --timeout=5s CMD python scripts/healthcheck.py
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","18201"]
