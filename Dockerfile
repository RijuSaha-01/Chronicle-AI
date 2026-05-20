# Chronicle AI - Docker Setup
# ===========================
# Multi-stage build for optimal image size and packaging efficiency

# --- Builder Stage ---
FROM python:3.11-slim as builder

WORKDIR /app

# Install system compilation dependencies required for building complex libraries (e.g. ChromaDB, mutagen)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies to user space
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# --- Production Stage ---
FROM python:3.11-slim

WORKDIR /app

# Install system runtime dependencies (ffmpeg is essential for audio tools like pydub/TTS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source, static, and helper script folders
COPY src/ ./src/
COPY static/ ./static/
COPY scripts/ ./scripts/

# Create persistent folder mount points in the container
RUN mkdir -p /data /config

# Default runtime environment variables
ENV PYTHONPATH=/app/src
ENV CHRONICLE_DATA_DIR=/data
ENV CHRONICLE_DB_PATH=/data/chronicle_ai.db
ENV CHRONICLE_CHROMA_DIR=/data/chroma
ENV CHRONICLE_EXPORTS_DIR=/data/exports
ENV CHRONICLE_CONFIG_DIR=/config
ENV OLLAMA_BASE_URL=http://ollama:11434
ENV OLLAMA_MODEL=llama3.2

# Expose FastAPI REST API port
EXPOSE 8000

# Health check to ensure the service is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run the FastAPI server using Uvicorn
CMD ["uvicorn", "chronicle_ai.api:app", "--host", "0.0.0.0", "--port", "8000"]
