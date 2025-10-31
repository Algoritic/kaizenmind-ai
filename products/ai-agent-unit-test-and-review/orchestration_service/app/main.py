import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from app.schemas import AnalyzeRequest, AnalyzeResponse, StatusResponse, CodeReviewRequest, RepoRequest, CompareRequest, LlmConfig
from threading import Thread
from typing import Dict, List
from app.github_mcp import mcp_client, post_pr_review_comment
from app.utils import new_task_dir, ARTIFACTS
from app.reporters import write_review_report

from app.langraph_agent import build_graph, AgentState
from langchain_openai import ChatOpenAI
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent Test Orchestrator")

TASKS: Dict[str, Dict] = {}

# Initialize LLM and Langraph Workflow
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
workflow = build_graph(llm)

def _run_langraph_task(tid: str, initial_state: AgentState):
    logger.info(f"Task {tid}: Starting langraph workflow with initial state: {initial_state}")
    try:
        TASKS[tid]["status"] = "running"
        final_state = workflow.invoke(initial_state)
        
        report_path = final_state.get("report_path")
        
        # If it was a code review, post the review to the PR
        if final_state.get("review_results") and final_state.get("pr_url"):
            logger.info(f"Task {tid}: Posting code review to PR: {final_state['pr_url']}")
            combined_review_body = f"{final_state['review_results']}\n\n---\n\n## 📝 Documentation Review\n{final_state.get('doc_review_results', '')}"
            post_result = post_pr_review_comment(final_state['pr_url'], combined_review_body)
            report_path = f"Review posted to PR: {post_result.get('html_url', final_state['pr_url'])}"

        TASKS[tid]["status"] = "done"
        TASKS[tid]["report_path"] = report_path
        logger.info(f"Task {tid}: Langraph workflow completed. Report path: {report_path}")
    except Exception as e:
        TASKS[tid]["status"] = "error"
        TASKS[tid]["error"] = str(e)
        logger.error(f"Task {tid}: Error during langraph workflow: {e}", exc_info=True)

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    logger.info(f"Received analyze request: {req.dict()}")
    if not (req.repo_url or req.upload_dir):
        logger.warning("Analyze request failed: Neither repo_url nor upload_dir provided.")
        raise HTTPException(400, "Provide repo_url or upload_dir")
    import uuid
    tid = str(uuid.uuid4())
    
    initial_state: AgentState = {
        "repo_src": req.repo_url or req.upload_dir,
        "languages": req.languages,
        "branch": req.branch,
        "llm_config": req.llm_config,
        "review_service_base_url": req.review_service_base_url,
        "pentest_service_base_url": req.pentest_service_base_url,
        "dynamic_pentest_requests": req.dynamic_pentest_requests,
        "next_step": "prepare_repo"
    }
    
    TASKS[tid] = {"status": "queued"}
    Thread(target=_run_langraph_task, args=(tid, initial_state), daemon=True).start()
    logger.info(f"Task {tid} created and queued for analysis.")
    return AnalyzeResponse(task_id=tid)

@app.post("/code-review", response_model=AnalyzeResponse)
async def code_review(req: CodeReviewRequest):
    logger.info(f"Received code review request: {req.dict()}")
    import uuid
    tid = str(uuid.uuid4())
    
    initial_state: AgentState = {
        "pr_url": req.pr_url,
        "llm_config": req.llm_config,
        "review_service_base_url": req.review_service_base_url,
        "pentest_service_base_url": "http://pentest_service:8000", # Not used in code review but required by state
        "next_step": "code_review"
    }
    
    TASKS[tid] = {"status": "queued"}
    Thread(target=_run_langraph_task, args=(tid, initial_state), daemon=True).start()
    logger.info(f"Task {tid} created and queued for code review.")
    return AnalyzeResponse(task_id=tid)

@app.get("/artifacts/{task_id}/{filename}")
async def get_artifact(task_id: str, filename: str):
    """Endpoint to serve generated artifact files for download."""
    
    base_dir = ARTIFACTS / task_id
    file_path = base_dir / filename
    
    logger.info(f"Attempting to serve artifact: {file_path}")
    
    if not file_path.exists():
        logger.warning(f"Artifact not found: {file_path}")
        raise HTTPException(404, "Artifact file not found")
    
    if '..' in str(file_path.relative_to(ARTIFACTS)):
        raise HTTPException(400, "Invalid path")
        
    media_type = "text/markdown" if file_path.suffix == ".md" else "application/octet-stream"
    
    return FileResponse(file_path, media_type=media_type, filename=filename)

@app.post("/repository/branches", response_model=List[str])
async def get_repository_branches(req: RepoRequest):
    logger.info(f"Received request for branches of repo: {req.repo_url}")
    try:
        branches = mcp_client.get_branches(req.repo_url)
        return branches
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error fetching branches for {req.repo_url}: {e}", exc_info=True)
        raise HTTPException(500, "Error fetching branches")

@app.post("/repository/compare", response_model=AnalyzeResponse)
async def compare_branches(req: CompareRequest):
    logger.info(f"Received compare request: {req.dict()}")
    import uuid
    tid = str(uuid.uuid4())
    TASKS[tid] = {"status": "queued"}
    # This still uses the old method, it can be migrated to langraph later
    Thread(target=_run_compare_task, args=(tid, req), daemon=True).start()
    logger.info(f"Task {tid} created and queued for compare task.")
    return AnalyzeResponse(task_id=tid)

@app.get("/status/{task_id}", response_model=StatusResponse)
async def status(task_id: str):
    logger.info(f"Received status request for task ID: {task_id}")
    if task_id not in TASKS:
        logger.warning(f"Status request failed: Task ID {task_id} not found.")
        raise HTTPException(404, "Task not found")
    t = TASKS[task_id]
    logger.info(f"Returning status for task {task_id}: {t['status']}")
    return StatusResponse(status=t["status"], report_path=t.get("report_path"), error=t.get("error"))

def _run_compare_task(tid: str, req: CompareRequest):
    logger.info(f"Task {tid}: Starting compare task for repo: {req.repo_url}, base: {req.base}, head: {req.head}")
    try:
        TASKS[tid]["status"] = "running"

        from app.agent import ReviewServiceClient
        review_service_client = ReviewServiceClient(
            base_url=req.review_service_base_url,
            llm_config=req.llm_config
        )
        
        diff = mcp_client.get_branch_diff(req.repo_url, req.base, req.head)
        logger.info(f"Task {tid}: Got branch diff. Length: {len(diff)}")
        
        review_body_result = review_service_client.perform_code_review(diff, req.prompt)
        review_body = review_body_result.get("review", "Critical Review Failed.")
        
        doc_review_result = review_service_client.perform_doc_review(diff, req.prompt)
        doc_.py
        doc_review = doc_review_result.get("review", "Documentation Review Failed.")
        
        combined_review_body = f"{review_body}\n\n---\n\n## 📝 Documentation Review\n{doc_review}"
        logger.info(f"Task {tid}: Generated combined review body.")
        
        temp_dir = new_task_dir(tid) 
        
        report_filename = f"review_compare_{req.base}_to_{req.head}.md"
        report_path = write_review_report(temp_dir, combined_review_body, report_filename)
        
        TASKS[tid]["status"] = "done"
        TASKS[tid]["report_path"] = report_path
        logger.info(f"Task {tid}: Compare task completed. Report path: {report_path}")
        
    except ValueError as e:
        TASKS[tid]["status"] = "error"
        TASKS[tid]["error"] = str(e)
        logger.error(f"Task {tid}: Invalid parameters for compare task: {e}", exc_info=True)
    except Exception as e:
        TASKS[tid]["status"] = "error"
        TASKS[tid]["error"] = str(e)
        logger.error(f"Task {tid}: Error during compare task: {e}", exc_info=True)
