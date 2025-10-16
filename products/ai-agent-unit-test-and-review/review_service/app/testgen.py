import os
from pathlib import Path
from typing import List, Dict
import logging
from openai import OpenAI 

logger = logging.getLogger(__name__)

SYSTEM_HINT = (
    "You generate minimal, deterministic unit tests with clear Arrange-Act-Assert, "
    "no network calls, and fast execution. Prefer pytest for Python, jest for Node, "
    "and JUnit (maven/gradle) for Java. Use dependency injection or mocking for I/O."
)

REVIEW_SYSTEM_HINT = (
    "You are a Senior Software Architect specializing in code review. "
    "Your goal is to provide a production-level critical review covering "
    "Technical correctness, Design, Security, and Maintainability. "
    "Output MUST be in Markdown format. Start with a summary, then provide "
    "detailed feedback under relevant headings: Security & Resilience, Design & Architecture, "
    "Technical Correctness & Performance, and Maintainability & Observability. "
    "Do not include any prose outside the review content."
)

# NEW: Initialize the OpenAI client globally. 
# It automatically picks up OPENAI_API_KEY and OPENAI_API_BASE from the environment.
try:
    client = OpenAI()
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {e}. Check DOCKER_HOST or VPN if needed.")
    # For safety in case of early errors, re-initialize if needed inside _llm 
    # or handle the exception by raising a runtime error in a proper environment.
    raise RuntimeError("Failed to initialize OpenAI client. Check environment configuration.")

def get_model():
    # Use OPENAI_MODEL env var, falling back to a powerful default
    return os.getenv("OPENAI_MODEL") or "gpt-4o" 

MODEL = get_model()

def _llm(prompt: str, is_review: bool = False) -> str:
    logger.debug(f"Calling LLM ({MODEL}) with prompt: {prompt[:200]}...")
    
    system_content = REVIEW_SYSTEM_HINT if is_review else SYSTEM_HINT
    
    messages = [
        {"role": "system", "content": system_content}, 
        {"role": "user", "content": prompt}
    ]

    try:
        # Use OpenAI client for chat completion
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=4000 if is_review else 1200
        )
        
        # Access content from the standard OpenAI SDK response object
        content = resp.choices[0].message.content
        logger.debug(f"LLM response received: {content[:200]}...")
        return content
            
    except Exception as e:
        logger.error(f"Error during LLM completion via OpenAI SDK: {e}")
        # Raise a more descriptive error
        raise RuntimeError(f"LLM Completion Failed. Check OPENAI_API_KEY validity and model name. Error: {e}") from e
     
def plan_test_targets(repo_meta: Dict, languages: List[str]) -> Dict[str, List[str]]:
    logger.info(f"Planning test targets for languages: {languages}")
    files = repo_meta.get("files", [])
    mapping: Dict[str, List[str]] = {"python": [], "node": [], "java": []}
    for f in files:
        if f.endswith(".py") and "/tests/" not in f:
            mapping["python"].append(f)
        if f.endswith((".js", ".ts")) and "/test" not in f.lower():
            mapping["node"].append(f)
        if f.endswith('.java') and "/test" not in f.lower():
            mapping["java"].append(f)
    for k in mapping:
        mapping[k] = mapping[k][:20]
    filtered_mapping = {k: v for k, v in mapping.items() if k in languages}
    logger.info(f"Planned test targets: {filtered_mapping}")
    return filtered_mapping

def gen_tests_for_file(lang: str, relpath: str, repo_root: Path) -> Dict[str, str]:
    logger.info(f"Generating tests for file: {relpath} (language: {lang})")
    code = (repo_root / relpath).read_text(encoding='utf-8', errors='ignore')
    prompt = f"""
Given this {lang} source file (relative path: {relpath}), write unit tests.
Constraints:
- Keep tests deterministic and side-effect free.
- Cover edge cases and error paths.
- Include setup/teardown if needed.
- Add minimal mocks for file/network/process.
- Use coverage-friendly patterns.
- Output ONLY the test file contents. Do not include prose.

<CODE>
{code[:4000]}
</CODE>
"""
    test_body = _llm(prompt)
    if lang == "python":
        test_path = Path("tests") / (Path(relpath).stem + "_test.py")
    elif lang == "node":
        test_path = Path("__tests__") / (Path(relpath).stem + ".test." + ("ts" if relpath.endswith(".ts") else "js"))
    else:  # java
        rp = Path(relpath)
        pkg = Path("src/test/java") / rp.parent.relative_to("src/main/java") if "src/main/java" in relpath else Path("src/test/java") / rp.parent
        test_path = pkg / (rp.stem + "Test.java")
    logger.info(f"Generated test path: {test_path} for {relpath}")
    return {"test_path": str(test_path), "content": test_body}

def gen_code_review(diff: str, prompt_override: str = None) -> str:
    """Generates a critical code review based on the provided diff."""
    review_prompt = f"""
Perform a CRITICAL code review on the following code changes (Git Diff).
Focus Areas: Technical, Design, Security, Maintainability.
Custom Instruction (if any): {prompt_override or 'None'}

<GIT_DIFF>
{diff[:15000]}
</GIT_DIFF>
"""
    # Call LLM with the review flag set to True
    return _llm(review_prompt, is_review=True)