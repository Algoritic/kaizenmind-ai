from pathlib import Path
from typing import Dict, List
import logging

from testgen import plan_test_targets, gen_tests_for_file, gen_code_review
from static_analysis import run_static_review

logger = logging.getLogger(__name__)

class ReviewAgent:
    def __init__(self):
        pass

    def plan_targets(self, repo_meta: Dict, languages: List[str]) -> Dict[str, List[str]]:
        logger.info(f"ReviewAgent: Planning test targets for languages: {languages}")
        return plan_test_targets(repo_meta, languages)

    def generate_tests(self, lang: str, relpath: str, repo_root: Path) -> Dict[str, str]:
        logger.info(f"ReviewAgent: Generating tests for file: {relpath} (language: {lang})")
        return gen_tests_for_file(lang, relpath, repo_root)

    def perform_static_review(self, lang: str, cwd: Path) -> Dict:
        logger.info(f"ReviewAgent: Running static review for language: {lang}")
        return run_static_review(lang, cwd)

    def perform_code_review(self, diff: str, prompt_override: str = None) -> str:
        logger.info("ReviewAgent: Performing code review.")
        return gen_code_review(diff, prompt_override)
