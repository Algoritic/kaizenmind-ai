from pydantic import BaseModel
from typing import List, Optional, Literal

class AnalyzeRequest(BaseModel):
    repo_url: Optional[str] = None
    upload_dir: Optional[str] = None  # Mounted path inside API container
    branch: Optional[str] = None
    languages: List[Literal["python", "node", "java"]] = ["python", "node", "java"]
    max_files: int = 2500

class AnalyzeResponse(BaseModel):
    task_id: str

class StatusResponse(BaseModel):
    status: Literal["queued", "running", "done", "error"]
    report_path: Optional[str] = None
    error: Optional[str] = None

class CodeReviewRequest(BaseModel):
    pr_url: str
    prompt: Optional[str] = None

class RepoRequest(BaseModel):
    repo_url: str

class CompareRequest(BaseModel):
    repo_url: str
    base: str
    head: str
    prompt: Optional[str] = None