FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including supervisor
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create supervisor log directory
RUN mkdir -p /var/log/supervisor

# Copy requirements first for better caching
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all necessary directories from parent context
COPY utils ./utils
COPY models ./models
COPY procedure ./procedure
COPY api ./api
COPY background ./background

# Copy supervisor configuration
COPY docker/supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set Python path to allow imports from parent directory
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check (检查 API 是否健康)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run supervisor to manage both API and task processor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
