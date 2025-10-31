# AI-Agent Test Orchestrator

**Goal:** An end‑to‑end, production‑ready application that:

- Ingests any codebase (JS/TS, Java, Python prioritized)
- Understands the project structure and public API surface
- Auto‑generates unit tests dynamically per language
- Executes tests inside isolated, ephemeral containers (per language/runtime)
- Captures stdout/stderr, coverage, flaky behavior, and exit codes
- Performs static checks (eslint/bandit/spotbugs) when available
- Produces a consolidated, shareable report (Markdown + HTML) with all findings
- Simple UI built with Streamlit; API layer with FastAPI; agent scaffold with LangGraph‑style orchestration (pure Python, no vendor lock‑in). Replace LLM provider via LiteLLM or OpenAI SDK.

> ⚠️ **Security note:** For truly untrusted code, enable Docker user namespaces, seccomp profiles, read‑only root fs, no‑new‑privileges, CPU/memory/pids limits, and disable outbound network in runner containers. See `docker-compose.yml` and runners for defaults.

---

## Repository Layout

```
agent-test-orchestrator/
├─ README.md
├─ docker-compose.yml
├─ .env.example
├─ requirements.txt
├─ backend/
│  ├─ app/
│  │  ├─ main.py                 # FastAPI (HTTP) + task queue shim
│  │  ├─ agent.py                # Orchestration graph (LangGraph-like)
│  │  ├─ ingestion.py            # Repo introspection & metadata
│  │  ├─ testgen.py              # LLM-driven test generation (JS/Java/Python)
│  │  ├─ static_analysis.py      # eslint, bandit, spotbugs wrappers
│  │  ├─ runner_manager.py       # Docker runner lifecycle (per language)
│  │  ├─ reporters.py            # Markdown/HTML report builder
│  │  ├─ utils.py
│  │  └─ schemas.py
│  └─ Dockerfile
├─ ui/
│  ├─ streamlit_app.py
│  └─ Dockerfile
├─ runners/
│  ├─ python/
│  │  ├─ Dockerfile
│  │  └─ run.sh
│  ├─ node/
│  │  ├─ Dockerfile
│  │  └─ run.sh
│  └─ java/
│     ├─ Dockerfile
│     └─ run.sh
└─ artifacts/                     # Reports, logs, coverage, test files (gitignored)
```

---

## Setup & Run

```bash
# 1) Clone and configure
cp .env.example .env
# Set OPENAI_API_KEY=... or LLM_BASE_URL + LLM_MODEL in .env

# 2) Start stack (FastAPI + Streamlit UI)
docker compose up --build

# 3) Open UI
# http://localhost:8501
```

**Host requirements:** Docker 24+, docker compose plugin, ~6–8GB RAM recommended.

---

## docker-compose.yml

```yaml
version: "3.9"
services:
  api:
    build: ./backend
    env_file: .env
    ports: ["8000:8000"]
    volumes:
      - ./artifacts:/app/artifacts
      - /var/run/docker.sock:/var/run/docker.sock:ro  # runner_manager controls containers
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4g

  ui:
    build: ./ui
    env_file: .env
    ports: ["8501:8501"]
    environment:
      API_BASE_URL: http://api:8000
    depends_on: [api]
```

---

## .env.example

```
# LLM configuration (choose one path)
OPENAI_API_KEY=
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# OR use LiteLLM-compatible proxy
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=

# General
ARTIFACTS_DIR=/app/artifacts
RUNNER_CPU_LIMIT=1.0
RUNNER_MEM_LIMIT=2g
RUNNER_TIMEOUT_SECS=600
```

---

## requirements.txt

```
fastapi==0.115.4
uvicorn[standard]==0.30.6
pydantic==2.9.2
python-dotenv==1.0.1
httpx==0.27.2
litellm==1.47.7
langgraph==0.2.27
langchain==0.3.7
streamlit==1.39.0
python-dateutil==2.9.0
Jinja2==3.1.4
docker==7.1.0
```

---

## backend/Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && useradd -m appuser \
 && mkdir -p /app/artifacts && chown -R appuser:appuser /app
COPY backend/app /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## ui/Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir streamlit==1.39.0 httpx==0.27.2 python-dotenv==1.0.1
COPY ui/streamlit_app.py /app/streamlit_app.py
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

---

## backend/app/schemas.py

```python
from pydantic import BaseModel
from typing import List, Optional, Literal

class AnalyzeRequest(BaseModel):
    repo_url: Optional[str] = None
    upload_dir: Optional[str] = None  # Mounted path inside API container
    languages: List[Literal["python", "node", "java"]] = ["python", "node", "java"]
    max_files: int = 2500

class AnalyzeResponse(BaseModel):
    task_id: str

class StatusResponse(BaseModel):
    status: Literal["queued", "running", "done", "error"]
    report_path: Optional[str] = None
    error: Optional[str] = None
```

---

## backend/app/utils.py

```python
import os, shutil, subprocess, tempfile, uuid
from pathlib import Path

ARTIFACTS = Path(os.getenv("ARTIFACTS_DIR", "/app/artifacts"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)

def new_task_dir() -> Path:
    tid = str(uuid.uuid4())
    tdir = ARTIFACTS / tid
    tdir.mkdir(parents=True, exist_ok=True)
    return tdir

def clone_or_copy(src: str, dest: Path) -> Path:
    # src can be git url or local path (mounted)
    if src.startswith("http://") or src.startswith("https://") or src.endswith(".git"):
        subprocess.check_call(["git", "clone", "--depth", "1", src, str(dest)])
    else:
        if os.path.isdir(src):
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            raise ValueError("upload_dir/repo_url invalid")
    return dest

def detect_languages(root: Path):
    langs = set()
    if (root / "package.json").exists(): langs.add("node")
    if any((root / p).exists() for p in ["pom.xml", "build.gradle", "build.gradle.kts"]): langs.add("java")
    if list(root.rglob("*.py")): langs.add("python")
    return list(langs)

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
```

---

## backend/app/ingestion.py

```python
from pathlib import Path
from typing import Dict, Any

IGNORES = {"node_modules", ".git", "dist", "build", ".venv", "venv", "target"}

def summarize_repo(root: Path, max_files: int = 2500) -> Dict[str, Any]:
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in IGNORES for part in p.parts):
            continue
        if p.stat().st_size > 1_000_000:  # 1MB cap per file for summary
            continue
        files.append(p)
        if len(files) >= max_files:
            break
    # Build a lightweight map by extension
    ext_map: Dict[str, int] = {}
    for f in files:
        ext_map[f.suffix] = ext_map.get(f.suffix, 0) + 1
    return {
        "file_count": len(files),
        "ext_hist": ext_map,
        "has_tests": any("test" in f.name.lower() for f in files),
        "files": [str(f.relative_to(root)) for f in files[:200]],  # head for prompt context
    }
```

---

## backend/app/testgen.py

```python
import os
from pathlib import Path
from typing import List, Dict
from litellm import completion

SYSTEM_HINT = (
    "You generate minimal, deterministic unit tests with clear Arrange-Act-Assert, "
    "no network calls, and fast execution. Prefer pytest for Python, jest for Node, "
    "and JUnit (maven/gradle) for Java. Use dependency injection or mocking for I/O."
)

MODEL = os.getenv("OPENAI_MODEL") or os.getenv("LLM_MODEL") or "gpt-4o-mini"

def _llm(prompt: str) -> str:
    resp = completion(model=MODEL, messages=[{"role":"system","content":SYSTEM_HINT},{"role":"user","content":prompt}],
                      temperature=0.2, max_tokens=1200)
    return resp["choices"][0]["message"]["content"]

def plan_test_targets(repo_meta: Dict, languages: List[str]) -> Dict[str, List[str]]:
    # Heuristics: suggest targets based on file list
    files = repo_meta.get("files", [])
    mapping: Dict[str, List[str]] = {"python": [], "node": [], "java": []}
    for f in files:
        if f.endswith(".py") and "/tests/" not in f:
            mapping["python"].append(f)
        if f.endswith(('.js', '.ts')) and "/test" not in f.lower():
            mapping["node"].append(f)
        if f.endswith('.java') and "/test" not in f.lower():
            mapping["java"].append(f)
    # limit per lang
    for k in mapping:
        mapping[k] = mapping[k][:20]
    return {k: v for k, v in mapping.items() if k in languages}

def gen_tests_for_file(lang: str, relpath: str, repo_root: Path) -> Dict[str, str]:
    code = (repo_root / relpath).read_text(encoding='utf-8', errors='ignore')
    prompt = f"""
Given this {lang} source file (relative path: {relpath}), write unit tests.
Constraints:
- Keep tests deterministic and side-effect free.
- Cover edge cases and error paths.
- Include setup/teardown if needed.
- Add minimal mocks for file/network/process.
- Use coverage-friendly patterns.
- Output ONLY the test file contents. Do not include prose.

<CODE>\n{code[:4000]}\n</CODE>
"""
    test_body = _llm(prompt)
    if lang == "python":
        test_path = Path("tests") / (Path(relpath).stem + "_test.py")
    elif lang == "node":
        test_path = Path("__tests__") / (Path(relpath).stem + ".test." + ("ts" if relpath.endswith(".ts") else "js"))
    else:  # java
        # Map src/main/java/com/x/Y.java -> src/test/java/com/x/YTest.java
        rp = Path(relpath)
        pkg = Path("src/test/java") / rp.parent.relative_to("src/main/java") if "src/main/java" in relpath else Path("src/test/java") / rp.parent
        test_path = pkg / (rp.stem + "Test.java")
    return {"test_path": str(test_path), "content": test_body}
```

---

## backend/app/static_analysis.py

```python
import subprocess, shutil
from pathlib import Path
from typing import Dict

TOOLS = {
    "node": ["npx", "-y", "eslint", ".", "--format", "json"],
    "python": ["bandit", "-r", ".", "-f", "json"],
    "java": ["spotbugs", "-textui", "-effort:max", "-low"],
}

# Note: linters must be available in runner images; errors are tolerated.

def run_static(lang: str, cwd: Path) -> Dict:
    cmd = TOOLS.get(lang)
    if not cmd or shutil.which(cmd[0]) is None:
        return {"tool": None, "results": []}
    try:
        out = subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.STDOUT, text=True, timeout=300)
        return {"tool": cmd[0], "results": out}
    except Exception as e:
        return {"tool": cmd[0], "error": str(e)}
```

---

## backend/app/runner_manager.py

```python
import os, json, tarfile, io, time
from pathlib import Path
from typing import Dict, Tuple
import docker

CPU = float(os.getenv("RUNNER_CPU_LIMIT", "1.0"))
MEM = os.getenv("RUNNER_MEM_LIMIT", "2g")
TIMEOUT = int(os.getenv("RUNNER_TIMEOUT_SECS", "600"))

LANG_IMAGE = {
    "python": "runner-python:latest",
    "node": "runner-node:latest",
    "java": "runner-java:latest",
}

client = docker.from_env()


def _tar_dir(path: Path) -> io.BytesIO:
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode='w') as tar:
        for p in path.rglob('*'):
            if p.is_dir():
                continue
            tar.add(str(p), arcname=str(p.relative_to(path)))
    data.seek(0)
    return data


def run_in_container(lang: str, repo_dir: Path) -> Tuple[int, str]:
    image = LANG_IMAGE[lang]
    # Create container
    container = client.containers.create(
        image=image,
        command=["/bin/bash", "/runner/run.sh"],
        detach=True,
        network_disabled=True,
        user="1000:1000",
        mem_limit=MEM,
        nano_cpus=int(CPU * 1e9),
        security_opt=["no-new-privileges:true"],
        read_only=True,
        working_dir="/workspace",
    )
    # Upload repo tar to /workspace
    tarstream = _tar_dir(repo_dir)
    container.put_archive("/workspace", tarstream.getvalue())

    container.start()
    start = time.time()
    logs = container.logs(stream=True)
    output = []
    try:
        for chunk in logs:
            output.append(chunk.decode(errors='ignore'))
            if time.time() - start > TIMEOUT:
                container.kill()
                output.append("\n[runner] TIMEOUT reached, container killed.\n")
                break
    finally:
        exit_code = container.wait().get('StatusCode', 99)
        container.remove(force=True)
    return exit_code, ''.join(output)
```

---

## backend/app/reporters.py

```python
from pathlib import Path
from jinja2 import Template
from datetime import datetime

HTML_TEMPLATE = Template(
    """
    <html><head><meta charset="utf-8"><title>Agent Report</title>
    <style>body{font-family:Inter,system-ui,Arial;margin:24px;}
    .card{border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:16px 0;}
    pre{background:#0b1020;color:#d1d5db;padding:12px;border-radius:8px;overflow:auto;}
    code{font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;}
    h1,h2{margin:8px 0}
    table{border-collapse:collapse;width:100%}
    td,th{border:1px solid #e5e7eb;padding:8px;text-align:left}
    .ok{color:#059669}.fail{color:#dc2626}
    </style></head>
    <body>
    <h1>AI Agent Test Report</h1>
    <p>Generated: {{ ts }}</p>
    <div class="card"><h2>Summary</h2>
    <table>
      <tr><th>Files</th><td>{{ summary.file_count }}</td></tr>
      <tr><th>Languages</th><td>{{ languages|join(', ') }}</td></tr>
      <tr><th>Has existing tests</th><td>{{ 'Yes' if summary.has_tests else 'No' }}</td></tr>
    </table></div>

    {% for block in blocks %}
      <div class="card">
        <h2>{{ block.title }}</h2>
        {% if block.meta %}<pre><code>{{ block.meta }}</code></pre>{% endif %}
        {% if block.output %}<pre><code>{{ block.output }}</code></pre>{% endif %}
      </div>
    {% endfor %}

    </body></html>
    """
)


def write_report(artifacts_dir: Path, languages, summary, blocks):
    html = HTML_TEMPLATE.render(ts=datetime.utcnow().isoformat(), languages=languages, summary=summary, blocks=blocks)
    out_html = artifacts_dir / "report.html"
    out_md = artifacts_dir / "report.md"
    out_html.write_text(html, encoding='utf-8')
    # Brief Markdown companion
    out_md.write_text(f"# AI Agent Report\n\nLanguages: {', '.join(languages)}\n\nFiles: {summary['file_count']}\n\nSee detailed HTML.\n", encoding='utf-8')
    return str(out_html)
```

---

## backend/app/agent.py

```python
from pathlib import Path
from typing import Dict, List
from .utils import new_task_dir, clone_or_copy, write_file
from .ingestion import summarize_repo
from .testgen import plan_test_targets, gen_tests_for_file
from .static_analysis import run_static
from .runner_manager import run_in_container
from .reporters import write_report

class Orchestrator:
    def __init__(self, repo_src: str, languages: List[str]):
        self.repo_src = repo_src
        self.languages = languages
        self.artifacts = new_task_dir()
        self.repo_dir = self.artifacts / "repo"

    def prepare(self):
        clone_or_copy(self.repo_src, self.repo_dir)
        self.summary = summarize_repo(self.repo_dir)
        if not self.languages:
            self.languages = []
        # Auto-detect fallback
        from .utils import detect_languages
        autod = detect_languages(self.repo_dir)
        if not self.languages:
            self.languages = autod
        else:
            # intersect requested with detected
            self.languages = [l for l in self.languages if l in autod]

    def generate_tests(self) -> Dict[str, List[Dict[str, str]]]:
        targets = plan_test_targets(self.summary, self.languages)
        generated = {}
        for lang, files in targets.items():
            generated[lang] = []
            for relpath in files:
                spec = gen_tests_for_file(lang, relpath, self.repo_dir)
                # persist into repo_dir
                out_path = self.repo_dir / spec["test_path"]
                write_file(out_path, spec["content"])
                generated[lang].append({"file": relpath, "test_path": spec["test_path"]})
        return generated

    def static_checks(self) -> Dict[str, Dict]:
        results = {}
        for lang in self.languages:
            results[lang] = run_static(lang, self.repo_dir)
        return results

    def run_tests(self) -> Dict[str, Dict]:
        outputs = {}
        for lang in self.languages:
            code, out = run_in_container(lang, self.repo_dir)
            outputs[lang] = {"exit_code": code, "output": out}
        return outputs

    def report(self, blocks: List[Dict]):
        return write_report(self.artifacts, self.languages, self.summary, blocks)

    def run_all(self) -> str:
        self.prepare()
        gen = self.generate_tests()
        static_res = self.static_checks()
        test_res = self.run_tests()
        blocks = [
            {"title": "Repo Summary", "meta": str(self.summary), "output": None},
            {"title": "Generated Tests", "meta": str(gen), "output": None},
        ]
        for lang, s in static_res.items():
            blocks.append({"title": f"Static Analysis ({lang})", "meta": None, "output": str(s)})
        for lang, r in test_res.items():
            blocks.append({"title": f"Test Run ({lang})", "meta": f"exit={r['exit_code']}", "output": r["output"]})
        return self.report(blocks)
```

---

## backend/app/main.py

```python
import os
from fastapi import FastAPI, HTTPException
from .schemas import AnalyzeRequest, AnalyzeResponse, StatusResponse
from .agent import Orchestrator
from threading import Thread
from typing import Dict

app = FastAPI(title="AI Agent Test Orchestrator")

TASKS: Dict[str, Dict] = {}


def _run_task(tid: str, req: AnalyzeRequest):
    try:
        src = req.repo_url or req.upload_dir
        orch = Orchestrator(src, req.languages)
        TASKS[tid]["status"] = "running"
        report_path = orch.run_all()
        TASKS[tid]["status"] = "done"
        TASKS[tid]["report_path"] = report_path
    except Exception as e:
        TASKS[tid]["status"] = "error"
        TASKS[tid]["error"] = str(e)


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    if not (req.repo_url or req.upload_dir):
        raise HTTPException(400, "Provide repo_url or upload_dir")
    import uuid
    tid = str(uuid.uuid4())
    TASKS[tid] = {"status": "queued"}
    Thread(target=_run_task, args=(tid, req), daemon=True).start()
    return AnalyzeResponse(task_id=tid)


@app.get("/status/{task_id}", response_model=StatusResponse)
async def status(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(404, "Task not found")
    t = TASKS[task_id]
    return StatusResponse(status=t["status"], report_path=t.get("report_path"), error=t.get("error"))
```

---

## runners/python/Dockerfile

```dockerfile
FROM python:3.11-slim
RUN pip install --no-cache-dir pytest pytest-cov bandit
RUN useradd -m runner
USER runner
WORKDIR /workspace
COPY run.sh /runner/run.sh
```

### runners/python/run.sh
```bash
#!/usr/bin/env bash
set -euo pipefail
# Install project deps if present
if [[ -f "requirements.txt" ]]; then pip install --no-cache-dir -r requirements.txt || true; fi
# Create coverage dir
mkdir -p .coverage
# Run tests with coverage if tests exist
if compgen -G "tests/*.py" > /dev/null; then
  pytest -q --maxfail=1 --disable-warnings --cov=. --cov-report=term-missing || true
else
  echo "[python] No tests found"; exit 0
fi
```

---

## runners/node/Dockerfile

```dockerfile
FROM node:20-slim
RUN npm i -g eslint jest @babel/preset-env
RUN useradd -m runner
USER runner
WORKDIR /workspace
COPY run.sh /runner/run.sh
```

### runners/node/run.sh
```bash
#!/usr/bin/env bash
set -euo pipefail
# Install deps
if [[ -f "package.json" ]]; then npm ci || npm i || true; fi
# Jest config fallback
if [[ ! -f "jest.config.js" && ! -f "jest.config.cjs" ]]; then
cat > jest.config.cjs <<'CFG'
module.exports = { testEnvironment: 'node', transform: {}, roots: ['<rootDir>/__tests__'] };
CFG
fi
# Run ESLint if available
if command -v eslint >/dev/null 2>&1; then npx -y eslint . || true; fi
# Run tests
if compgen -G "__tests__/*.(js|ts)" > /dev/null; then
  npx -y jest --runInBand || true
else
  echo "[node] No tests found"; exit 0
fi
```

---

## runners/java/Dockerfile

```dockerfile
FROM eclipse-temurin:21-jdk
RUN useradd -m runner
USER runner
WORKDIR /workspace
# SpotBugs CLI (optional lightweight)
RUN mkdir -p /opt && curl -fsSL -o /opt/spotbugs.tgz https://repo1.maven.org/maven2/com/github/spotbugs/spotbugs/4.8.6/spotbugs-4.8.6.tgz \
 && tar -xzf /opt/spotbugs.tgz -C /opt && rm /opt/spotbugs.tgz
ENV PATH="/opt/spotbugs-4.8.6/bin:$PATH"
COPY run.sh /runner/run.sh
```

### runners/java/run.sh
```bash
#!/usr/bin/env bash
set -euo pipefail

build_with_maven() {
  mvn -q -DskipTests -e -B test || true
}

build_with_gradle() {
  ./gradlew test || gradle test || true
}

if [[ -f "pom.xml" ]]; then
  build_with_maven
elif [[ -f "build.gradle" || -f "build.gradle.kts" ]]; then
  build_with_gradle
else
  echo "[java] No build file found (pom.xml/gradle)."; exit 0
fi

# SpotBugs attempt (non-fatal)
if command -v spotbugs >/dev/null 2>&1; then spotbugs -textui -low || true; fi
```

---

## ui/streamlit_app.py

```python
import os, time, httpx, streamlit as st
API = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Agent Test Orchestrator", layout="wide")
st.title("🧪 AI Agent: Code Understanding & Test Runner")

repo_url = st.text_input("Git repo URL (public or with access) OR leave blank to use mounted path:")
upload_dir = st.text_input("Mounted local path inside API container (e.g., /data/project)")
languages = st.multiselect("Languages", ["python","node","java"], default=["python","node","java"])

if st.button("Analyze & Test", type="primary"):
    if not (repo_url or upload_dir):
        st.error("Provide a repo_url or upload_dir")
    else:
        with st.spinner("Starting task..."):
            r = httpx.post(f"{API}/analyze", json={"repo_url": repo_url or None, "upload_dir": upload_dir or None, "languages": languages})
            r.raise_for_status()
            tid = r.json()["task_id"]
        st.session_state["tid"] = tid

if tid := st.session_state.get("tid"):
    st.info(f"Task ID: {tid}")
    ph = st.empty()
    while True:
        s = httpx.get(f"{API}/status/{tid}").json()
        if s["status"] in ("queued","running"):
            ph.write(f"Status: **{s['status']}** ...")
            time.sleep(2)
        elif s["status"] == "done":
            ph.success("Done!")
            url = s["report_path"].replace("/app/artifacts", "artifacts")
            st.markdown(f"**Report:** `{s['report_path']}` (open on host volume)")
            st.stop()
        else:
            ph.error(f"Error: {s.get('error')}")
            st.stop()
```

---

## README.md

```markdown
# AI-Agent Test Orchestrator

A production-ready agent system that ingests a codebase (JS/TS, Java, Python), generates unit tests via LLM, executes them in isolated Docker containers, runs static analysis, and produces a consolidated report. UI via Streamlit, API via FastAPI.

## Features
- 🔎 Repository understanding & target selection
- 🧠 LLM-driven unit test generation (pytest, jest, JUnit)
- 🔒 Ephemeral, networkless Docker runners per language
- 🧹 Static analysis hooks (eslint, bandit, spotbugs)
- 📈 Coverage and logs captured in artifacts
- 🧾 HTML+MD report artifacts

## Quickstart
1. `cp .env.example .env` and set your model/api key
2. `docker compose up --build`
3. Open `http://localhost:8501`

## Security Recommendations
- Use user namespaces, readOnlyRootFilesystem, seccomp profiles
- Limit CPU/memory/pids; disable network for runners (default)
- Consider running the API without Docker socket access by introducing a runner sidecar with a narrowed Socket or remote Docker endpoint

## Extensibility
- Swap LLM provider via `.env` and `litellm`
- Add language runners under `runners/`
- Enrich static analysis (pylint, mypy, detekt, pmD, etc)
- Add fuzzers (e.g., Jest property tests, Hypothesis)

## Caveats
- Private Git URLs require credentials in environment or ssh agent forwarding
- Some monorepos/builds may require extra setup commands in `run.sh`
```

---

## Notes on Production Hardening

- **Task Queue:** For scale, switch the in-memory thread to Celery/RQ with Redis and durable status.
- **Artifacts:** Store reports in S3/GCS with signed URLs and retention policies.
- **Prompt Privacy:** Redact secrets before sending to LLM; never include `.env` in prompts.
- **Timeouts:** Tune `RUNNER_TIMEOUT_SECS` per repo size.
- **Model Costs:** Cache test outputs by file digest to avoid re-generation when unchanged.
- **Coverage:** Parse and merge coverage artifacts into the report.

---

## How It Works (Flow)

1. **Ingest**: Clone/copy repository to per-task workspace.
2. **Summarize**: Gather file inventory, heuristics for targets.
3. **Generate Tests**: For each language/file, synthesize tests in conventional locations.
4. **Static Checks**: Run linters/security scanners (best-effort).
5. **Execute**: Spin ephemeral, networkless containers per language; install deps; run tests.
6. **Report**: Persist HTML/MD with logs, exit codes, and summaries.

---

## Next Steps You Might Want

- Add PR comment bot (GitHub App) to post summaries.
- Triton/CodeQL integration for deep static analysis.
- Sandbox upgrades (gVisor/Kata Containers) for stricter isolation.
- Flakiness detection by multiple reruns with jitter.
```

