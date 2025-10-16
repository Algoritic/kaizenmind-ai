import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse # NEW IMPORT
from app.schemas import AnalyzeRequest, AnalyzeResponse, StatusResponse, CodeReviewRequest, RepoRequest, CompareRequest
from app.agent import Orchestrator
from threading import Thread
from typing import Dict, List
# Import the posting function from the modular client
from app.github_mcp import mcp_client, post_pr_review_comment
# NEW IMPORTS for Review Service Client
from app.agent import ReviewServiceClient # Import the client from agent.py
# NEW IMPORTS from utilities and reporters
from app.utils import new_task_dir, ARTIFACTS
from app.reporters import write_review_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent Test Orchestrator")

TASKS: Dict[str, Dict] = {}

# Initialize Review Service Client
review_service_client = ReviewServiceClient(base_url="http://review_service:8000")

def _run_task(tid: str, req: AnalyzeRequest):
    logger.info(f"Task {tid}: Starting analysis for source: {req.repo_url or req.upload_dir}")
    try:
        src = req.repo_url or req.upload_dir
        orch = Orchestrator(src, req.languages, req.branch)
        TASKS[tid]["status"] = "running"
        logger.info(f"Task {tid}: Orchestrator initialized, running all steps.")
        report_path = orch.run_all()
        TASKS[tid]["status"] = "done"
        TASKS[tid]["report_path"] = report_path
        logger.info(f"Task {tid}: Analysis completed. Report path: {report_path}")
    except Exception as e:
        TASKS[tid]["status"] = "error"
        TASKS[tid]["error"] = str(e)
        logger.error(f"Task {tid}: Error during analysis: {e}", exc_info=True)

def _run_code_review_task(tid: str, req: CodeReviewRequest):
    logger.info(f"Task {tid}: Starting code review for PR: {req.pr_url}")
    try:
        TASKS[tid]["status"] = "running"
        
        # 1. Fetch Diff
        diff = mcp_client.get_pr_diff(req.pr_url)
        logger.info(f"Task {tid}: Got PR diff. Length: {len(diff)}")

        # 2. Generate Review using Review Service
        review_body = review_service_client.perform_code_review(diff, req.prompt)
        logger.info(f"Task {tid}: Generated review body.")

        # 3. Post Review to PR
        # This function uses the configured GITHUB_API_BASE_URL (MCP or GitHub)
        post_result = post_pr_review_comment(req.pr_url, review_body.get("review", "")) # Assuming review_body is a dict with a 'review' key
        report_path = f"Review posted to PR: {post_result.get('html_url', req.pr_url)}"

        TASKS[tid]["status"] = "done"
        TASKS[tid]["report_path"] = report_path
        logger.info(f"Task {tid}: Code review completed and posted. Report path: {report_path}")
    except ValueError as e:
        TASKS[tid]["status"] = "error"
        TASKS[tid]["error"] = str(e)
        logger.error(f"Task {tid}: Invalid PR URL provided: {e}", exc_info=True)
    except Exception as e:
        TASKS[tid]["status"] = "error"
        TASKS[tid]["error"] = str(e)
        logger.error(f"Task {tid}: Error during code review: {e}", exc_info=True)

def _run_compare_task(tid: str, req: CompareRequest):
    logger.info(f"Task {tid}: Starting compare task for repo: {req.repo_url}, base: {req.base}, head: {req.head}")
    try:
        TASKS[tid]["status"] = "running"
        
        # 1. Fetch Diff
        diff = mcp_client.get_branch_diff(req.repo_url, req.base, req.head)
        logger.info(f"Task {tid}: Got branch diff. Length: {len(diff)}")
        
        # 2. Generate Review using Review Service (reusing the critical review prompt)
        review_body = review_service_client.perform_code_review(diff, req.prompt)
        logger.info(f"Task {tid}: Generated review body.")
        
        # 3. Create Artifacts Directory 
        temp_dir = new_task_dir(tid) # Use the tid to create the task-specific directory
        
        # 4. Write Markdown Report
        report_filename = f"review_compare_{req.base}_to_{req.head}.md"
        report_path = write_review_report(temp_dir, review_body.get("review", ""), report_filename) # Assuming review_body is a dict with a 'review' key
        
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

# NEW ENDPOINT TO SERVE ARTIFACTS FOR DOWNLOAD
@app.get("/artifacts/{task_id}/{filename}")
async def get_artifact(task_id: str, filename: str):
    """Endpoint to serve generated artifact files for download."""
    
    # Construct the safe file path
    base_dir = ARTIFACTS / task_id
    file_path = base_dir / filename
    
    logger.info(f"Attempting to serve artifact: {file_path}")
    
    if not file_path.exists():
        logger.warning(f"Artifact not found: {file_path}")
        raise HTTPException(404, "Artifact file not found")
    
    # Simple security check to prevent path traversal
    if '..' in str(file_path.relative_to(ARTIFACTS)):
        raise HTTPException(400, "Invalid path")
        
    media_type = "text/markdown" if file_path.suffix == ".md" else "application/octet-stream"
    
    return FileResponse(file_path, media_type=media_type, filename=filename)

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    logger.info(f"Received analyze request: {req.dict()}")
    if not (req.repo_url or req.upload_dir):
        logger.warning("Analyze request failed: Neither repo_url nor upload_dir provided.")
        raise HTTPException(400, "Provide repo_url or upload_dir")
    import uuid
    tid = str(uuid.uuid4())
    TASKS[tid] = {"status": "queued"}
    Thread(target=_run_task, args=(tid, req), daemon=True).start()
    logger.info(f"Task {tid} created and queued for analysis.")
    return AnalyzeResponse(task_id=tid)

@app.post("/code-review", response_model=AnalyzeResponse)
async def code_review(req: CodeReviewRequest):
    logger.info(f"Received code review request: {req.dict()}")
    import uuid
    tid = str(uuid.uuid4())
    TASKS[tid] = {"status": "queued"}
    Thread(target=_run_code_review_task, args=(tid, req), daemon=True).start()
    logger.info(f"Task {tid} created and queued for code review.")
    return AnalyzeResponse(task_id=tid)

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