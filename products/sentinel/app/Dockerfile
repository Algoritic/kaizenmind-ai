FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 1) system deps + ca-certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git curl \
 && rm -rf /var/lib/apt/lists/*

# 2) add your corporate/Zscaler cert and register it
# (needs to end with .crt and live in /usr/local/share/ca-certificates/)
COPY zscaler.crt /usr/local/share/ca-certificates/zscaler.crt
RUN update-ca-certificates

# 3) tell Python/pip/requests to use the system bundle (belt-and-suspenders)
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY pyproject.toml /app/pyproject.toml

RUN python -m pip install --upgrade pip \
 && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi \
 && pip install "langgraph>=0.2.0" "pydantic>=2" "streamlit>=1.28"

COPY src /app/src
COPY ui /app/ui
COPY reports /app/reports

ENV PYTHONPATH=/app/src
EXPOSE 8501
