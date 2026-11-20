FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml .
# Runtime dependencies, aligned with the tested environment (requirements-lock.txt,
# haystack-ai 3.4.1). The previous pin (haystack-ai==2.31.1) installed a different
# major version inside the image than the one the test suite exercises.
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic pydantic-settings python-dotenv httpx haystack-ai==3.4.1
ENV HAYSTACK_TELEMETRY_ENABLED=False
RUN python -m venv /opt/indobert \
    && /opt/indobert/bin/pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && /opt/indobert/bin/pip install --no-cache-dir transformers
ENV NUSANTARA_INDOBERT_PYTHON=/opt/indobert/bin/python \
    NUSANTARA_INDOBERT_WORKER=/app/nusantara-models/indobert_worker.py \
    HF_HOME=/app/data/huggingface
COPY app ./app
COPY control-plane/dist ./control-plane/dist
COPY docs ./docs
COPY .env.example ./
COPY scripts/healthcheck.py ./scripts/healthcheck.py
COPY nusantara-models/indobert_worker.py ./nusantara-models/indobert_worker.py
RUN useradd -r -u 10001 appuser && mkdir -p /app/data /home/appuser && chown -R appuser:appuser /app /home/appuser
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python scripts/healthcheck.py
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
