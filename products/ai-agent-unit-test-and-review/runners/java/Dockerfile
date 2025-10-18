FROM eclipse-temurin:21-JDK
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client
RUN useradd -m runner
USER runner
WORKDIR /workspace
# SpotBugs CLI (optional lightweight)
RUN mkdir -p /opt && curl -fsSL -o /opt/spotbugs.tgz https://repo1.maven.org/maven2/com/github/spotbugs/spotbugs/4.8.6/spotbugs-4.8.6.tgz \
 && tar -xzf /opt/spotbugs.tgz -C /opt && rm /opt/spotbugs.tgz
ENV PATH="/opt/spotbugs-4.8.6/bin:$PATH"
ENV SSH_AUTH_SOCK /home/runner/.ssh/ssh_agent_sock
RUN mkdir -p /home/runner/.ssh
COPY run.sh /runner/run.sh
