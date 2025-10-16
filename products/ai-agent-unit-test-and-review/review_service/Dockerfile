FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && apt-get update && apt-get install -y --no-install-recommends sudo git openssh-client \
 && useradd -m appuser \
 && usermod -aG sudo appuser \
 && mkdir -p /app/artifacts && chown -R appuser:appuser /app \
 && mkdir -p /app/.ssh
ENV SSH_AUTH_SOCK /app/.ssh/ssh_agent_sock
ENV PYTHONPATH=/app
COPY app /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]