from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from pathlib import Path

from testgen import gen_tests_for_file, gen_code_review, plan_test_targets, analyze_docs_for_diff
from static_analysis import run_static_review
from schemas import LlmConfig # Import LlmConfig

app = FastAPI()

class GenerateTestsRequest(BaseModel):
    lang: str
    relpath: str
    repo_root: str # This will be a path to a cloned repo in the service
    llm_config: Optional[LlmConfig] = None

class CodeReviewRequest(BaseModel):
    diff: str
    prompt_override: str = None
    llm_config: Optional[LlmConfig] = None

class StaticReviewRequest(BaseModel):
    lang: str
    cwd: str
    llm_config: Optional[LlmConfig] = None # For consistency, even if not directly used

class PlanTestTargetsRequest(BaseModel):
    repo_meta: Dict
    languages: List[str]
    llm_config: Optional[LlmConfig] = None

@app.post("/plan_test_targets")
async def plan_targets(request: PlanTestTargetsRequest):
    return plan_test_targets(request.repo_meta, request.languages, request.llm_config)

@app.post("/generate_tests")
async def generate_tests(request: GenerateTestsRequest):
    try:
        result = gen_tests_for_file(request.lang, request.relpath, Path(request.repo_root), request.llm_config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/code_review")
async def code_review(request: CodeReviewRequest):
    try:
        review = gen_code_review(request.diff, request.prompt_override, request.llm_config)
        return {"review": review}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/static_review")
async def static_review(request: StaticReviewRequest):
    try:
        results = run_static_review(request.lang, Path(request.cwd), request.llm_config)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NEW ENDPOINT: Documentation Review
@app.post("/doc_review")
async def doc_review(request: CodeReviewRequest):
    """Generates a documentation-focused review based on the provided diff."""
    try:
        review = analyze_docs_for_diff(request.diff, request.llm_config)
        return {"review": review}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))