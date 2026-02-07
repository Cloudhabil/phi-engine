FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy package
COPY . /app/phi_engine_pkg/

# Install with demo extras
RUN pip install --no-cache-dir -e "/app/phi_engine_pkg[demo,api]"

# Expose ports: Webhook (4242), Streamlit (8501), API (8200)
EXPOSE 4242 8501 8200

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:8200/health || exit 1

# Start all services via a simple shell script
COPY phi_engine_pkg/phi_engine/demo/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
