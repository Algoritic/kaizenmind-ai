import os, shutil, subprocess, tempfile, uuid
from pathlib import Path

ARTIFACTS = Path(os.getenv("ARTIFACTS_DIR", "/app/artifacts"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)

def new_task_dir(tid: str = None) -> Path: # MODIFIED to accept tid
    if tid is None:
        tid = str(uuid.uuid4())
    tdir = ARTIFACTS / tid
    tdir.mkdir(parents=True, exist_ok=True)
    return tdir

def clone_or_copy(src: str, dest: Path, branch: str = None) -> Path:
    # src can be git url or local path (mounted)
    if src.startswith("http://") or src.startswith("https://") or src.endswith(".git"):
        cmd = ["git", "clone", "--depth", "1"]
        if branch:
            cmd.extend(["--branch", branch])
        cmd.extend([src, str(dest)])
        subprocess.check_call(cmd)
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