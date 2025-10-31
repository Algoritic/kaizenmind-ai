FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps (git helpful; add build tools if needed)
RUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only dependency files first for better caching if you rebuild later
COPY requirements.txt /app/requirements.txt
# If pyproject.toml exists, copy too (optional)
COPY pyproject.toml /app/pyproject.toml

# Install python deps (best-effort for missing extras)
RUN pip install --upgrade pip \
 && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi \
 && pip install "langgraph>=0.2.0" "pydantic>=2" "streamlit>=1.28"

# Copy source
COPY src /app/src
COPY ui /app/ui
COPY reports /app/reports

# Ensure src on PYTHONPATH
ENV PYTHONPATH=/app/src

# Default port for Streamlit
EXPOSE 8501
