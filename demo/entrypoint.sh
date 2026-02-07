#!/bin/bash
# Start all phi-engine demo services

# Webhook server (background)
python -m phi_engine.demo.webhook &

# API server (background)
python -m phi_engine.api.server &

# Streamlit app (foreground)
streamlit run /app/phi_engine_pkg/phi_engine/demo/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
