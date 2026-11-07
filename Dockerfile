# 1. Base
FROM python:3.12-slim

# 2-4. Set-up
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/hf
WORKDIR /app
RUN useradd --create-home appuser
# Only the empty folder: a chown after files exist copies them into a new layer.
RUN chown appuser /app

# 5-7. Slow stuff: packages as root (CPU torch first), then the two models as appuser
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt
USER appuser
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('BAAI/bge-small-en-v1.5'); CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# 8. Only what serving needs: no PDFs, evals or tests. Owned by root, so appuser can read but not change it.
COPY api.py ./
COPY rag/ rag/
COPY static/ static/
COPY data/chunks.jsonl data/
COPY corpus/SOURCES.md corpus/download.py corpus/

# Trace metadata. Late in the file, so a new commit rebuilds only the layers below.
# Build: docker build --build-arg GIT_COMMIT=$(git rev-parse --short HEAD) -t rag-api:<version> .
# Run: docker run -e APP_ENV=uat ... (defaults to docker)
ARG GIT_COMMIT=unknown
ENV GIT_COMMIT=$GIT_COMMIT APP_ENV=docker

# 9-11. Run
EXPOSE 8000
CMD ["uvicorn", "api:api", "--host", "0.0.0.0", "--port", "8000"]