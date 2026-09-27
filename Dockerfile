FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1 \
    FASTEMBED_CACHE_PATH=/opt/fastembed

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Bake the embedding model into the image so the container starts without downloading it
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5')"

COPY app ./app
COPY scripts ./scripts
COPY data ./data

# SQLite database and generated DPR PDFs live on volumes (see docker-compose.yml)
RUN mkdir -p /app/storage /app/static/dprs

EXPOSE 8000

CMD ["sh", "-c", "python scripts/wait_for_services.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
