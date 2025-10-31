# Pentest AI 
A containerized app to perform deep scan and test of the code and build, running locally with Docker.

## Components
- Docker
- Compose
- CLI
- UI (Steramlit)

* Contents of the repo:

  * `Dockerfile`
  * `docker-compose.yml`
  * `src/pentestai/cli.py` (simple one-shot CLI runner)
  * `src/pentestai/langgraph_graphs/hybrid_review_graph.py` (hybrid parallel graph)
  * `src/pentestai/models/persona_results.py` (Pydantic)
  * `src/pentestai/tools/adapters/*` (adapter layer)
  * `reports/` (sample JSON + Markdown)

---

### 🐳 Option A — Streamlit UI

```bash
# from the unzipped project root
docker compose up --build app
```

Then open: `http://localhost:8501`

Your local codebase to analyze: put it in `./target` (host), which is mounted at `/app/target` (container).

---

### 🐍 Option B — One-shot CLI run (writes to ./reports)

```bash
# Put a repo to scan in ./target on your host first
docker compose run --rm cli

# Or specify an APK instead of a repo:
# docker compose run --rm cli python -m pentestai.cli --apk /app/target/app.apk
# sudo docker-compose run --rm cli python -m pentestai.cli --repo /app/target
```

Outputs:

* `./reports/final_report.json`
* `./reports/final_report.md`

---

### 🔧 Dockerfile (already included)

* Based on `python:3.11-slim`
* Installs deps (`requirements.txt` if present) + `langgraph`, `pydantic`, `streamlit`
* Sets `PYTHONPATH=/app/src`
* Default command runs Streamlit

---

### 🧩 docker-compose.yml (already included)

* `app` service (UI): maps `./target` → `/app/target`, `./reports` → `/app/reports`
* `cli` service (profile: `cli`): runs the hybrid flow once against `/app/target`

If you need to pass secrets later (e.g., LLM keys), export `OPENAI_API_KEY` in your shell or `.env`—compose will forward it.

---

If you want me to:

* wire **real** Semgrep/Bandit/Pytest/ZAP/MobSF instead of stubs,
* add a **Makefile** (`make build`, `make run`, `make scan-repo=...`),
* or add a **GitHub Actions** CI workflow,

tell me your preference and I’ll ship it.
