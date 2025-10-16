from pathlib import Path
from typing import Dict, List
from app.utils import new_task_dir, clone_or_copy, write_file
from app.ingestion import summarize_repo
from app.runner_manager import run_in_container
from app.reporters import write_report
import logging
import requests # For making HTTP requests to other services

logger = logging.getLogger(__name__)

# Placeholder client for Review Service
class ReviewServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def perform_code_review(self, diff: str, prompt_override: str = None) -> Dict:
        payload = {"diff": diff}
        if prompt_override:
            payload["prompt_override"] = prompt_override
        response = requests.post(f"{self.base_url}/code_review", json=payload)
        response.raise_for_status()
        return response.json()

    def plan_test_targets(self, repo_meta: Dict, languages: List[str]) -> Dict[str, List[str]]:
        response = requests.post(f"{self.base_url}/plan_test_targets", json={'repo_meta': repo_meta, 'languages': languages})
        response.raise_for_status()
        return response.json()

    def generate_tests(self, lang: str, relpath: str, repo_root: str) -> Dict[str, str]:
        response = requests.post(f"{self.base_url}/generate_tests", json={'lang': lang, 'relpath': relpath, 'repo_root': repo_root})
        response.raise_for_for_status()
        return response.json()

    def static_review(self, lang: str, cwd: str) -> Dict:
        response = requests.post(f"{self.base_url}/static_review", json={'lang': lang, 'cwd': cwd})
        response.raise_for_status()
        return response.json()

# Placeholder client for Pentest Service
class PentestServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def static_pentest(self, lang: str, cwd: str) -> Dict:
        response = requests.post(f"{self.base_url}/static_pentest", json={'lang': lang, 'cwd': cwd})
        response.raise_for_status()
        return response.json()

class Orchestrator:
    def __init__(self, repo_src: str, languages: List[str], branch: str = None):
        self.repo_src = repo_src
        self.languages = languages
        self.branch = branch
        self.artifacts = new_task_dir()
        self.repo_dir = self.artifacts / "repo"
        self.review_service = ReviewServiceClient(base_url="http://review_service:8000") # Assuming review service runs on port 8000
        self.pentest_service = PentestServiceClient(base_url="http://pentest_service:8000") # Assuming pentest service runs on port 8000
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

    def run_tests(self) -> Dict[str, Dict]:
        logger.info("Running generated tests.")
        outputs = {}
        for lang in self.languages:
            logger.info(f"Running tests for language: {lang}")
            code, out = run_in_container(lang, self.repo_dir)
            outputs[lang] = {"exit_code": code, "output": out}
            logger.info(f"Tests for {lang} completed with exit code {code}.")
        return outputs

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
        test_res = self.run_tests()
        logger.info("Test runs complete.")
        blocks = [
            {"title": "Repo Summary", "meta": str(self.summary), "output": None},
            {"title": "Generated Tests", "meta": str(gen), "output": None},
        ]
        for lang, s_res in static_res.items():
            if "review" in s_res:
                blocks.append({"title": f"Static Review ({lang})", "meta": None, "output": str(s_res["review"])})
            if "pentest" in s_res:
                blocks.append({"title": f"Static Pentest ({lang})", "meta": None, "output": str(s_res["pentest"])})
        for lang, r in test_res.items():
            blocks.append({"title": f"Test Run ({lang})", "meta": f"exit={r['exit_code']}", "output": r["output"]})
        report_path = self.report(blocks)
        logger.info(f"Full analysis run complete. Report generated at: {report_path}")
        return report_path