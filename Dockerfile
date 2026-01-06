# Chronicle AI Docker Image
# =========================
# Multi-stage build for smaller final image

FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ ./src/
COPY static/ ./static/
COPY scripts/ ./scripts/

# Create exports directory
RUN mkdir -p exports/daily exports/weekly

# Set environment variables
ENV PYTHONPATH=/app/src
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV CHRONICLE_EXPORTS_DIR=/app/exports

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run the API server
CMD ["uvicorn", "chronicle_ai.api:app", "--host", "0.0.0.0", "--port", "8000"]
