FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic pydantic-settings python-dotenv httpx
COPY app ./app
COPY docs ./docs
COPY .env.example ./
RUN useradd -r -u 10001 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python scripts/healthcheck.py
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
