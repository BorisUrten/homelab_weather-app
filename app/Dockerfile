FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including curl for health checks)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better cache utilization
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash weatherapp && \
    chown -R weatherapp:weatherapp /app

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER weatherapp

# Expose port for API (can be overridden)
EXPOSE 8000

# Default command runs the collector
# This can be overridden in docker-compose.yml or when running the container
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "api:app", "--timeout", "120"]