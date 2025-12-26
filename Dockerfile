# MEM Study API - Fly.io Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/ ./scripts/
COPY config/ ./config/

# Content directory will be mounted as a volume
# If no volume, create empty directory
RUN mkdir -p /app/content

# Expose port
EXPOSE 8080

# Start FastAPI with uvicorn
CMD ["uvicorn", "scripts.api:app", "--host", "0.0.0.0", "--port", "8080"]
