import os
from pathlib import Path
from typing import List, Dict, Optional
import logging
from openai import OpenAI 
from schemas import LlmConfig # Import LlmConfig from app.schemas

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

# Dedicated System Hint for Doc Review
DOC_REVIEW_SYSTEM_HINT = (
    "You are a Documentation Expert. Your task is to review the provided code changes (Git Diff) "
    "and identify gaps in documentation (docstrings, README updates) for public interfaces. "
    "Output MUST be in Markdown format. Start with a summary of documentation quality, then provide "
    "detailed, actionable suggestions under a 'Documentation Suggestions' heading. "
    "If a public function/class is missing a docstring, generate a high-quality suggestion. "
    "Do not include any prose outside the review content."
)

# NEW: Initialize the OpenAI client globally. 
# It automatically picks up OPENAI_API_KEY and OPENAI_API_BASE from the environment.
def _llm(prompt: str, system_hint: str, llm_config: Optional[LlmConfig] = None, max_tokens: int = 1200) -> str:
    logger.debug(f"Calling LLM with prompt: {prompt[:200]}...")
    
    _client = None
    model_name = ""
    temperature = llm_config.llm_temperature if llm_config and llm_config.llm_temperature is not None else 0.2

    if llm_config and llm_config.llm_provider == "azure":
        from openai import AzureOpenAI
        api_key = llm_config.azure_openai_api_key or os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = llm_config.azure_openai_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment_name = llm_config.azure_openai_deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        model_name = deployment_name # Azure uses deployment name as model

        if not all([api_key, endpoint, deployment_name]):
            raise ValueError("Azure OpenAI configuration missing: API Key, Endpoint, or Deployment Name.")
        
        _client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2024-02-01", # Use a recent API version
        )
    else: # Default to OpenAI
        api_key = llm_config.openai_api_key if llm_config and llm_config.openai_api_key else os.getenv("OPENAI_API_KEY")
        model_name = llm_config.openai_model if llm_config and llm_config.openai_model else (os.getenv("OPENAI_MODEL") or "gpt-4o")

        if not api_key:
            raise ValueError("OpenAI API Key is missing.")

        _client = OpenAI(api_key=api_key)

    if not _client:
        raise RuntimeError("LLM client could not be initialized.")

    # Determine max_tokens based on the type of operation or explicit config
    if llm_config and llm_config.llm_max_tokens_review and system_hint == REVIEW_SYSTEM_HINT:
        max_tokens = llm_config.llm_max_tokens_review
    elif llm_config and llm_config.llm_max_tokens_doc_review and system_hint == DOC_REVIEW_SYSTEM_HINT:
        max_tokens = llm_config.llm_max_tokens_doc_review
    elif llm_config and llm_config.llm_max_tokens_testgen and system_hint == SYSTEM_HINT:
        max_tokens = llm_config.llm_max_tokens_testgen
    # Fallback to default max_tokens if not overridden or specific hint not matched
    elif system_hint == REVIEW_SYSTEM_HINT:
        max_tokens = 4000
    elif system_hint == DOC_REVIEW_SYSTEM_HINT:
        max_tokens = 2000
    else:
        max_tokens = 1200 # Default for testgen

    messages = [
        {"role": "system", "content": system_hint}, 
        {"role": "user", "content": prompt}
    ]

    try:
        # Use OpenAI client for chat completion
        resp = _client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Access content from the standard OpenAI SDK response object
        content = resp.choices[0].message.content
        logger.debug(f"LLM response received: {content[:200]}...")
        return content
            
    except Exception as e:
        logger.error(f"Error during LLM completion via OpenAI SDK: {e}")
        # Raise a more descriptive error
        raise RuntimeError(f"LLM Completion Failed. Check API key, endpoint, deployment name, and model name. Error: {e}") from e
     
def plan_test_targets(repo_meta: Dict, languages: List[str], llm_config: Optional[LlmConfig] = None) -> Dict[str, List[str]]:
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

def gen_tests_for_file(lang: str, relpath: str, repo_root: Path, llm_config: Optional[LlmConfig] = None) -> Dict[str, str]:
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
    test_body = _llm(prompt, system_hint=SYSTEM_HINT, llm_config=llm_config)
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

# gen_code_review now calls _llm with explicit review system hint and max tokens
def gen_code_review(diff: str, prompt_override: str = None, llm_config: Optional[LlmConfig] = None) -> str:
    """Generates a critical code review based on the provided diff."""
    review_prompt = f"""
Perform a CRITICAL code review on the following code changes (Git Diff).
Focus Areas: Technical, Design, Security, Maintainability.
Custom Instruction (if any): {prompt_override or 'None'}

<GIT_DIFF>
{diff[:15000]}
</GIT_DIFF>
"""
    # Use REVIEW_SYSTEM_HINT and set max_tokens for full review
    return _llm(review_prompt, system_hint=REVIEW_SYSTEM_HINT, llm_config=llm_config)

# Documentation Agent Tool
def analyze_docs_for_diff(diff: str, llm_config: Optional[LlmConfig] = None) -> str:
    """Generates a documentation review based on the provided diff."""
    doc_prompt = f"""
Analyze the following Git Diff for documentation gaps (docstrings, comments, README).
Provide suggestions for missing or unclear documentation.

<GIT_DIFF>
{diff[:15000]}
</GIT_DIFF>
"""
    # Use DOC_REVIEW_SYSTEM_HINT and limit tokens for a focused response
    return _llm(doc_prompt, system_hint=DOC_REVIEW_SYSTEM_HINT, llm_config=llm_config)