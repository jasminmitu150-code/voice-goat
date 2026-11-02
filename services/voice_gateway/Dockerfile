FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e ".[dev]"

COPY services/ /app/services/

EXPOSE 8000

CMD ["uvicorn", "services.voice_gateway.app:app", "--host", "0.0.0.0", "--port", "8000"]
