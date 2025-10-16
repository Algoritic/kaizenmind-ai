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