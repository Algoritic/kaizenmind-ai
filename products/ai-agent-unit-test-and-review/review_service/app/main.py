from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

from testgen import gen_tests_for_file, gen_code_review, plan_test_targets
from static_analysis import run_static_review

app = FastAPI()

class GenerateTestsRequest(BaseModel):
    lang: str
    relpath: str
    repo_root: str # This will be a path to a cloned repo in the service

class CodeReviewRequest(BaseModel):
    diff: str
    prompt_override: str = None

class StaticReviewRequest(BaseModel):
    lang: str
    cwd: str

class PlanTestTargetsRequest(BaseModel):
    repo_meta: Dict
    languages: List[str]

@app.post("/plan_test_targets")
async def plan_targets(request: PlanTestTargetsRequest):
    return plan_test_targets(request.repo_meta, request.languages)

@app.post("/generate_tests")
async def generate_tests(request: GenerateTestsRequest):
    try:
        # In a real scenario, repo_root would point to a temporary cloned repo
        # For now, we'll assume the path is accessible within the service container
        result = gen_tests_for_file(request.lang, request.relpath, Path(request.repo_root))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/code_review")
async def code_review(request: CodeReviewRequest):
    try:
        review = gen_code_review(request.diff, request.prompt_override)
        return {"review": review}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/static_review")
async def static_review(request: StaticReviewRequest):
    try:
        results = run_static_review(request.lang, Path(request.cwd))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
