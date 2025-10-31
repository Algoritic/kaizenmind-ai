from pydantic import BaseModel
from typing import List, Optional, Literal

class LlmConfig(BaseModel):
    llm_provider: str = "openai"
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens_review: Optional[int] = None
    llm_max_tokens_testgen: Optional[int] = None
    llm_max_tokens_doc_review: Optional[int] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment_name: Optional[str] = None

class DynamicPentestRequest(BaseModel):
    tool: str
    args: List[str]

class AnalyzeRequest(BaseModel):
    repo_url: Optional[str] = None
    upload_dir: Optional[str] = None  # Mounted path inside API container
    branch: Optional[str] = None
    languages: List[Literal["python", "node", "java"]] = ["python", "node", "java"]
    max_files: int = 2500
    llm_config: Optional[LlmConfig] = None
    review_service_base_url: Optional[str] = None
    pentest_service_base_url: Optional[str] = None
    dynamic_pentest_requests: Optional[List[DynamicPentestRequest]] = None

class AnalyzeResponse(BaseModel):
    task_id: str

class StatusResponse(BaseModel):
    status: Literal["queued", "running", "done", "error"]
    report_path: Optional[str] = None
    error: Optional[str] = None

class CodeReviewRequest(BaseModel):
    pr_url: str
    prompt: Optional[str] = None
    llm_config: Optional[LlmConfig] = None
    review_service_base_url: Optional[str] = None
    pentest_service_base_url: Optional[str] = None

class RepoRequest(BaseModel):
    repo_url: str

class CompareRequest(BaseModel):
    repo_url: str
    base: str
    head: str
    prompt: Optional[str] = None
    llm_config: Optional[LlmConfig] = None
    review_service_base_url: Optional[str] = None
    pentest_service_base_url: Optional[str] = None