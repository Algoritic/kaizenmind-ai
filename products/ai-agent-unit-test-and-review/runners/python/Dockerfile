FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client
RUN pip install --no-cache-dir pytest pytest-cov bandit
RUN useradd -m runner
USER runner
WORKDIR /workspace
ENV SSH_AUTH_SOCK /home/runner/.ssh/ssh_agent_sock
RUN mkdir -p /home/runner/.ssh
COPY run.sh /runner/run.sh