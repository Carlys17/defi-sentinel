FROM python:3.11-slim AS base

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Create non-root user
RUN useradd --create-home defi-sentinel && chown -R defi-sentinel:defi-sentinel /app
USER defi-sentinel

# Expose metrics port
EXPOSE 9090

# Default command
CMD ["defi-sentinel", "start"]