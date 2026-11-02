# VoiceRAG Service Dockerfile
# Knowledge base assistant demonstrating LLM08: Vector/Embedding Weaknesses

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e ".[dev,rag]"

# Copy application code
COPY services/ /app/services/

# Create knowledge base directory
RUN mkdir -p /app/knowledge_base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "services.voicerag.app:app", "--host", "0.0.0.0", "--port", "8000"]
