# PentestAI (download-free bootstrap)
- Multi-persona agent with LangGraph fallback
- Tool-first approach (Bandit/Semgrep/ESLint/pytest/Ghidra/ADB/Nmap)
- Works with Ollama or OpenAI-compatible LLMs
- Streamlit UI included

## Quickstart
```bash
pip install -r requirements.txt
pip install -e .
pentestai --git https://github.com/virattt/dexter.git --out artifacts_dexter
# UI:
streamlit run ui/streamlit_app.py
```

