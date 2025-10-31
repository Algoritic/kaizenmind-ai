from pathlib import Path
from typing import Dict, List, Tuple, Optional
from app.utils import new_task_dir, clone_or_copy, write_file
from app.ingestion import summarize_repo
from app.runner_manager import run_in_container
from app.reporters import write_report, parse_python_coverage_xml
import logging
import requests # For making HTTP requests to other services
from app.schemas import LlmConfig # Import LlmConfig

logger = logging.getLogger(__name__)

class ReviewServiceClient:
    def __init__(self, base_url: str, llm_config: Optional[LlmConfig]):
        self.base_url = base_url
        self.llm_config = llm_config

    def _prepare_payload(self, original_payload: Dict) -> Dict:
        if self.llm_config:
            original_payload["llm_config"] = self.llm_config.dict()
        return original_payload

    def plan_test_targets(self, summary: str, languages: List[str]) -> Dict:
        payload = self._prepare_payload({"summary": summary, "languages": languages})
        response = requests.post(f"{self.base_url}/plan_test_targets", json=payload)
        response.raise_for_status()
        return response.json()

    def generate_tests(self, lang: str, relpath: str, repo_dir: str) -> Dict:
        payload = self._prepare_payload({"lang": lang, "relpath": relpath, "repo_dir": repo_dir})
        response = requests.post(f"{self.base_url}/generate_tests", json=payload)
        response.raise_for_status()
        return response.json()

    def static_review(self, lang: str, cwd: str) -> Dict:
        payload = self._prepare_payload({"lang": lang, "cwd": cwd})
        response = requests.post(f"{self.base_url}/static_review", json=payload)
        response.raise_for_status()
        return response.json()

    def perform_code_review(self, diff: str, prompt: str) -> Dict:
        payload = self._prepare_payload({"diff": diff, "prompt": prompt})
        response = requests.post(f"{self.base_url}/code_review", json=payload)
        response.raise_for_status()
        return response.json()

    def perform_doc_review(self, diff: str, prompt: str) -> Dict:
        payload = self._prepare_payload({"diff": diff, "prompt": prompt})
        response = requests.post(f"{self.base_url}/doc_review", json=payload)
        response.raise_for_status()
        return response.json()

class PentestServiceClient:
    def __init__(self, base_url: str, llm_config: Optional[LlmConfig]):
        self.base_url = base_url
        self.llm_config = llm_config # Pentest service might not use LLM config directly, but pass it for consistency

    def _prepare_payload(self, original_payload: Dict) -> Dict:
        if self.llm_config:
            original_payload["llm_config"] = self.llm_config.dict()
        return original_payload

    def static_pentest(self, lang: str, cwd: str) -> Dict:
        payload = self._prepare_payload({"lang": lang, "cwd": cwd})
        response = requests.post(f"{self.base_url}/static_pentest", json=payload)
        response.raise_for_status()
        return response.json()

    def dynamic_pentest(self, tool: str, args: List[str]) -> Dict:
        payload = {"tool": tool, "args": args}
        response = requests.post(f"{self.base_url}/dynamic_pentest", json=payload)
        response.raise_for_status()
        return response.json()

class Orchestrator:
    def __init__(
        self, 
        repo_src: str, 
        languages: List[str], 
        branch: str = None, 
        llm_config: Optional[LlmConfig] = None,
        review_service_base_url: str = "http://review_service:8000",
        pentest_service_base_url: str = "http://pentest_service:8000"
    ):
        self.repo_src = repo_src
        self.languages = languages
        self.branch = branch
        self.artifacts = new_task_dir()
        self.repo_dir = self.artifacts / "repo"
        self.review_service = ReviewServiceClient(base_url=review_service_base_url, llm_config=llm_config)
        self.pentest_service = PentestServiceClient(base_url=pentest_service_base_url, llm_config=llm_config)
        logger.info(f"Orchestrator initialized for repo: {repo_src}, languages: {languages}, branch: {branch}")

    def prepare(self):
        logger.info(f"Preparing repository from {self.repo_src} to {self.repo_dir}")
        clone_or_copy(self.repo_src, self.repo_dir, self.branch)
        self.summary = summarize_repo(self.repo_dir)
        logger.info(f"Repository summarized. Detected languages: {self.languages}")
        if not self.languages:
            self.languages = []
        # Auto-detect fallback
        from utils import detect_languages
        autod = detect_languages(self.repo_dir)
        if not self.languages:
            self.languages = autod
            logger.info(f"No languages specified, auto-detected: {self.languages}")
        else:
            # intersect requested with detected
            initial_languages = self.languages
            self.languages = [l for l in self.languages if l in autod]
            logger.info(f"Intersected requested languages {initial_languages} with auto-detected {autod}. Final languages: {self.languages}")

    def generate_tests(self) -> Dict[str, List[Dict[str, str]]]:
        logger.info("Planning test targets via Review Service.")
        targets = self.review_service.plan_test_targets(self.summary, self.languages)
        logger.info(f"Test targets planned: {targets}")
        generated = {}
        for lang, files in targets.items():
            generated[lang] = []
            for relpath in files:
                logger.info(f"Generating tests for {relpath} in {lang} via Review Service")
                spec = self.review_service.generate_tests(lang, relpath, str(self.repo_dir))
                out_path = self.repo_dir / spec["test_path"]
                write_file(out_path, spec["content"])
                generated[lang].append({"file": relpath, "test_path": spec["test_path"]})
                logger.info(f'Generated test for {relpath}: {spec["test_path"]}')
        return generated

    def static_checks(self) -> Dict[str, Dict]:
        logger.info("Running static checks via Review and Pentest Services.")
        results = {}
        for lang in self.languages:
            logger.info(f"Running static review for language: {lang} via Review Service")
            review_results = self.review_service.static_review(lang, str(self.repo_dir))
            logger.info(f"Running static pentest for language: {lang} via Pentest Service")
            pentest_results = self.pentest_service.static_pentest(lang, str(self.repo_dir))
            results[lang] = {"review": review_results, "pentest": pentest_results}
            logger.info(f"Static analysis for {lang} completed.")
        return results

    def run_tests(self) -> Tuple[Dict, Dict]:
        logger.info("Running generated tests and collecting artifacts.")
        outputs = {}
        coverage_data = {} # NEW: To store parsed coverage summary
        for lang in self.languages:
            logger.info(f"Running tests for language: {lang}")
            # MODIFIED: run_in_container now returns container_files
            code, out, files = run_in_container(lang, self.repo_dir) 
            outputs[lang] = {"exit_code": code, "output": out}
            logger.info(f"Tests for {lang} completed with exit code {code}.")
            
            # NEW: Process Python coverage data
            if lang == "python" and "coverage.xml" in files:
                logger.info("Python coverage.xml artifact found. Parsing...")
                coverage_data["python"] = parse_python_coverage_xml(files["coverage.xml"])
                logger.info(f"Python overall coverage: {coverage_data['python'].get('overall_coverage', 'N/A')}")

        return outputs, coverage_data

    def report(self, blocks: List[Dict]):
        return write_report(self.artifacts, self.languages, self.summary, blocks)

    def run_all(self) -> str:
        logger.info("Starting full analysis run.")
        self.prepare()
        logger.info("Preparation complete.")
        gen = self.generate_tests()
        logger.info("Test generation complete.")
        static_res = self.static_checks()
        logger.info("Static checks complete.")
        test_res, cov_res = self.run_tests() # MODIFIED: Capture coverage data
        logger.info("Test runs and artifact collection complete.")
        blocks = [
            {"title": "Repo Summary", "meta": str(self.summary), "output": None},
            {"title": "Generated Tests", "meta": str(gen), "output": None},
        ]
        
        # Add Static Review and Pentest results
        for lang, s_res in static_res.items():
            if "review" in s_res:
                blocks.append({"title": f"Static Review ({lang})", "meta": None, "output": str(s_res["review"])})
            if "pentest" in s_res:
                blocks.append({"title": f"Static Pentest ({lang})", "meta": None, "output": str(s_res["pentest"])})
        
        # Add Test Run and Coverage Summary Blocks (NEW)
        for lang, r in test_res.items():
            blocks.append({"title": f"Test Run ({lang})", "meta": f"exit={r['exit_code']}", "output": r["output"]})
        
        if cov_res:
            for lang, data in cov_res.items():
                # Format coverage data for human review
                details = "\n".join([f"- {d['name']}: {d['coverage']} ({d['missed']} missed)" for d in data.get('file_details', [])])
                cov_output = (
                    f"Overall Coverage: {data.get('overall_coverage', 'N/A')}\n"
                    f"Total Lines: {data.get('total_lines', 0)}\n"
                    f"Missed Lines: {data.get('missed_lines', 0)}\n\n"
                    f"File-Level Summary (Top 5):\n{details}\n\n"
                    f"Error: {data.get('error') or 'None'}"
                )
                blocks.append({"title": f"Coverage Analysis ({lang})", "meta": None, "output": cov_output})
            
        report_path = self.report(blocks)
        logger.info(f"Full analysis run complete. Report generated at: {report_path}")
        return report_path