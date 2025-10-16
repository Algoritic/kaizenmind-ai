# runner.py (or wherever your function lives)
import os, io, time, tarfile
from pathlib import Path
from typing import Tuple
import docker
from docker.errors import DockerException, APIError

CPU = float(os.getenv("RUNNER_CPU_LIMIT", "1.0"))
MEM = os.getenv("RUNNER_MEM_LIMIT", "2g")
TIMEOUT = int(os.getenv("RUNNER_TIMEOUT_SECS", "600"))

LANG_IMAGE = {
    "python": "runner-python:latest",
    "node": "runner-node:latest",
    "java": "runner-java:latest",
}

def _tar_dir(path: Path) -> io.BytesIO:
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode='w') as tar:
        for p in path.rglob('*'):
            if p.is_dir():
                continue
            tar.add(str(p), arcname=str(p.relative_to(path)))
    data.seek(0)
    return data

def _get_docker_client() -> docker.DockerClient:
    """
    Create a Docker-compatible client that works with Podman Desktop.
    Honors DOCKER_HOST (tcp://, unix://, ssh://) and auto-negotiates API version.
    """
    # If using SSH (Podman machine), you must have pip-installed docker[ssh].
    base_url = os.getenv("DOCKER_HOST")  # e.g. tcp://host.containers.internal:2375 or ssh://root@host.containers.internal:63134/run/podman/podman.sock
    client = docker.DockerClient(base_url=base_url or None, version="auto")
    try:
        client.ping()
    except DockerException as e:
        raise RuntimeError(
            "Cannot reach Docker-compatible API. "
            "Check DOCKER_HOST (Podman Desktop: enable Docker API TCP), or SSH key if using ssh://. "
            f"Underlying error: {e}"
        )
    return client

def run_in_container(lang: str, repo_dir: Path) -> Tuple[int, str]:
    image = LANG_IMAGE[lang]
    client = _get_docker_client()

    container = None
    try:
        # Create container (read-only rootfs for safety, but tmpfs at /workspace so we can write)
        container = client.containers.create(
            image=image,
            command=["/bin/bash", "-lc", "/runner/run.sh"],
            detach=True,
            network_disabled=True,
            user="1000:1000",  # ensure your /runner/run.sh is readable; or drop this to run as image default
            mem_limit=MEM,
            nano_cpus=int(CPU * 1e9),
            security_opt=["no-new-privileges:true"],
            read_only=True,
            working_dir="/workspace",
            tmpfs={"/workspace": ""},  # <-- critical for put_archive with read_only rootfs
        )

        # Upload repo
        tarstream = _tar_dir(repo_dir)
        container.put_archive("/workspace", tarstream.getvalue())

        # Run and stream logs with timeout
        container.start()
        start = time.time()
        output_chunks = []
        for chunk in container.logs(stream=True):
            output_chunks.append(chunk.decode(errors='ignore'))
            if time.time() - start > TIMEOUT:
                container.kill()
                output_chunks.append("\n[runner] TIMEOUT reached, container killed.\n")
                break

        exit_code = container.wait().get('StatusCode', 99)
        return exit_code, ''.join(output_chunks)

    except (APIError, DockerException, PermissionError) as e:
        return 98, f"[runner] Docker/Podman error: {e}"
    except Exception as e:
        return 97, f"[runner] Unexpected error: {e}"
    finally:
        if container is not None:
            try:
                container.remove(force=True)
            except Exception:
                pass
