import subprocess, shutil
from pathlib import Path
from typing import Dict

TOOLS = {
    "node": ["npx", "-y", "eslint", ".", "--format", "json"],
    # Add other code quality tools here for different languages
}

def run_static_review(lang: str, cwd: Path) -> Dict:
    cmd = TOOLS.get(lang)
    if not cmd or shutil.which(cmd[0]) is None:
        return {"tool": None, "results": []}
    try:
        out = subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.STDOUT, text=True, timeout=300)
        return {"tool": cmd[0], "results": out}
    except Exception as e:
        return {"tool": cmd[0], "error": str(e)}
