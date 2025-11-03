#!/usr/bin/env bash
set -euo pipefail

# setup_and_run.sh
# Usage: ./setup_and_run.sh
# Detects OS, installs Ollama, asks for model to pull (default: gpt-oss:20b),
# builds docker compose and runs the test run command.

DEFAULT_MODEL="gpt-oss:20b"
REPO_TARGET="/app/target/dexter"
DOCKER_TEST_CMD="docker-compose run --rm cli python -m pentestai.cli --repo ${REPO_TARGET}"

echoinfo() { printf "\n[INFO] %s\n" "$*"; }
echoerr() { printf "\n[ERROR] %s\n" "$*" >&2; }

# Detect OS
OS_NAME="$(uname -s 2>/dev/null || echo "Windows")"
echoinfo "Detected OS: $OS_NAME"

install_ollama_mac() {
  echoinfo "Installing Ollama on macOS..."
  if command -v brew >/dev/null 2>&1; then
    echoinfo "Homebrew found — installing via 'brew install ollama'..."
    brew install ollama || {
      echoerr "Homebrew install failed. Trying official install script..."
      /bin/bash -c "$(curl -fsSL https://ollama.com/install.sh)"
    }
  else
    echoinfo "Homebrew not found — using Ollama official install script..."
    /bin/bash -c "$(curl -fsSL https://ollama.com/install.sh)"
  fi
}

install_ollama_linux() {
  echoinfo "Installing Ollama on Linux using official install script..."
  # Official install script supports Linux distros (calls apt/rpm as needed).
  # Might require sudo.
  if [ "$EUID" -ne 0 ]; then
    echoinfo "Sudo will be used for installation if required."
    /bin/bash -c "curl -fsSL https://ollama.com/install.sh | sh"
  else
    /bin/bash -c "curl -fsSL https://ollama.com/install.sh | sh"
  fi
}

install_ollama_windows() {
  echoinfo "Attempting Ollama install on Windows via winget (PowerShell)..."
  if command -v winget >/dev/null 2>&1; then
    echoinfo "winget found — attempting to install Ollama..."
    # Run via powershell to ensure proper privilege handling on native Windows
    powershell -NoProfile -Command "winget install --id=Ollama.Ollama -e --accept-package-agreements --accept-source-agreements" \
      && echoinfo "winget installation requested. Please follow any GUI prompts."
  else
    echoerr "winget not found. Please install Ollama manually from https://ollama.com/download (choose Windows) or enable winget."
    return 1
  fi
}

pull_model() {
  local model="$1"
  echoinfo "Pulling model: $model (this can take time and disk space)..."
  if ! command -v ollama >/dev/null 2>&1; then
    echoerr "ollama CLI not found in PATH after install. Please ensure Ollama installed correctly and retry."
    return 1
  fi

  # Try pull (this is the documented cli: ollama pull <model>)
  if ollama pull "$model"; then
    echoinfo "Model pulled successfully: $model"
  else
    echoerr "Failed to pull model: $model. Check your network and Ollama version (some models need latest Ollama)."
    return 1
  fi
}

build_docker_compose() {
  echoinfo "Building Docker Compose images..."
  # Prefer new Docker CLI (docker compose), fallback to docker-compose
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    if docker compose build; then
      echoinfo "Docker Compose build (docker compose) succeeded."
      return 0
    else
      echoerr "docker compose build failed. Trying docker-compose..."
    fi
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    if docker-compose build; then
      echoinfo "Docker Compose build (docker-compose) succeeded."
      return 0
    else
      echoerr "docker-compose build failed. Please inspect output and retry."
      return 1
    fi
  fi

  echoerr "Neither 'docker compose' nor 'docker-compose' found. Please install Docker Compose / Docker Desktop."
  return 1
}

run_test_command() {
  echoinfo "Running test command:"
  printf "  %s\n\n" "$DOCKER_TEST_CMD"
  # Execute using same form the user provided (docker-compose run ...)
  if docker-compose run --rm cli python -m pentestai.cli --repo /app/target/dexter; then
    echoinfo "Test run completed (exit code 0)."
  else
    echoerr "Test run failed — please check container logs."
    return 1
  fi
}

# MAIN
case "$OS_NAME" in
  Darwin*)
    install_ollama_mac
    ;;
  Linux*)
    install_ollama_linux
    ;;
  MINGW*|MSYS*|CYGWIN*|Windows_NT)
    # On Git Bash/WSL, prefer Linux flow. If native Windows, call PowerShell winget.
    if [ -n "${WSL_DISTRO_NAME-}" ]; then
      echoinfo "WSL detected — using Linux installer inside WSL."
      install_ollama_linux
    else
      install_ollama_windows || echoinfo "Windows installer path incomplete; continuing but Ollama may not be present."
    fi
    ;;
  *)
    echoerr "Unsupported OS: $OS_NAME. Please install Ollama manually: https://ollama.com/download"
    ;;
esac

# Verify ollama exists
if ! command -v ollama >/dev/null 2>&1; then
  echoerr "ollama CLI not found. If running on Windows please ensure you ran this script in an elevated PowerShell or install Ollama manually: https://ollama.com/download"
  echoinfo "Continuing to docker build step (Ollama not strictly required for docker build), but model pull will be skipped."
fi

# Ask which model to pull
read -r -p "Enter model to pull (default: ${DEFAULT_MODEL}): " USER_MODEL
USER_MODEL="${USER_MODEL:-$DEFAULT_MODEL}"

if command -v ollama >/dev/null 2>&1; then
  if ! pull_model "$USER_MODEL"; then
    echoerr "Model pull failed. You can try again manually: ollama pull ${USER_MODEL}"
    # continue to docker build anyway
  fi
else
  echoinfo "Skipping model pull (ollama missing)."
fi

# Build docker compose (may require sudo)
if ! build_docker_compose; then
  echoerr "Docker build failed. If you need elevated permissions, re-run this script with sudo or run 'sudo docker compose build' / 'sudo docker-compose build'."
  exit 1
fi

# Run the test run command the user requested.
echoinfo "Now running the test run command (this mounts your ./target as /app/target inside container):"
echoinfo "${DOCKER_TEST_CMD}"
if ! run_test_command; then
  echoerr "Test run failed. You can try manually:"
  printf "  %s\n" "$DOCKER_TEST_CMD"
  exit 1
fi

# Final instructions for the user
cat <<'INSTR'

✅ Done (or at least tried). Quick primer on how to use the system from here:

To run the CLI against the repo at ./target/dexter (same test command used above):
  docker-compose run --rm cli python -m pentestai.cli --repo /app/target/dexter

If you want to run the Streamlit UI:
  docker-compose up -d app
Then open a browser to: http://localhost:8501

If Ollama model pull failed earlier, you can pull manually:
  ollama pull gpt-oss:20b
You can list available local models with:
  ollama ls

Notes & troubleshooting:
* On macOS prefer Homebrew install (`brew install ollama`) or the official script at https://ollama.com/install.sh. :contentReference[oaicite:1]{index=1}
* On Linux use the official script: `curl -fsSL https://ollama.com/install.sh | sh`. :contentReference[oaicite:2]{index=2}
* On native Windows, try: `winget install --id=Ollama.Ollama -e` from an elevated PowerShell. If winget is not present, download from https://ollama.com/download. :contentReference[oaicite:3]{index=3}
* To pull the OpenAI-backed local model used by the default, run: `ollama pull gpt-oss:20b`. :contentReference[oaicite:4]{index=4}

If you want, I can:
* produce a PowerShell variant for pure Windows users,
* add an option to start the Ollama service automatically (on Linux/macOS),
* or modify the script to accept CLI flags (e.g. `--model`).

INSTR
