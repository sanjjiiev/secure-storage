# =====================================================
# Dockerfile - API Gateway (FastAPI)
# =====================================================

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Copy tests into container
COPY ../tests/ /app/tests/ 2>/dev/null || true

# Create shared mount point
RUN mkdir -p /shared

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
