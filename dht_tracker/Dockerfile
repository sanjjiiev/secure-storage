# =====================================================
# Dockerfile - DHT Tracker
# =====================================================

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

EXPOSE 8500

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8500", "--log-level", "info"]
