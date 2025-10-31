from typing import TypedDict, List, Dict, Optional
from pathlib import Path
import logging

from app.schemas import LlmConfig
from app.utils import new_task_dir, clone_or_copy, detect_languages, write_file
from app.ingestion import summarize_repo
from app.agent import ReviewServiceClient, PentestServiceClient
from app.runner_manager import run_in_container
from app.reporters import parse_python_coverage_xml, write_report

from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """
    Represents the state of the agent throughout the analysis process.
    """
    repo_src: str
    languages: List[str]
    branch: Optional[str]
    llm_config: Optional[LlmConfig]
    artifacts_dir: Path
    repo_dir: Path
    summary: Optional[str]
    generated_tests: Optional[Dict[str, List[Dict[str, str]]]]
    static_results: Optional[Dict[str, Dict]]
    test_results: Optional[Dict]
    coverage_results: Optional[Dict]
    report_path: Optional[str]
    review_service_base_url: str
    pentest_service_base_url: str
    pr_url: Optional[str]  # For code reviews
    review_results: Optional[str]
    doc_review_results: Optional[str]
    dynamic_pentest_results: Optional[Dict]
    next_step: str # This will be set by the router

def dynamic_pentest_node(state: AgentState) -> AgentState:
    logger.info("Performing dynamic pentesting.")
    pentest_service = PentestServiceClient(
        base_url=state['pentest_service_base_url'],
        llm_config=state['llm_config']
    )
    results = {}
    if state.get('dynamic_pentest_requests'):
        for req in state['dynamic_pentest_requests']:
            logger.info(f"Running dynamic pentest with tool: {req['tool']}")
            results[req['tool']] = pentest_service.dynamic_pentest(req['tool'], req['args'])
    else:
        logger.info("No dynamic pentest requests found in the state.")
        results = {"status": "not_configured", "details": "No dynamic pentest requests were provided."}

    logger.info("Dynamic pentesting completed.")
    return {**state, "dynamic_pentest_results": results}


def code_review_node(state: AgentState) -> AgentState:
    logger.info(f"Performing code review for PR: {state['pr_url']}")
    review_service = ReviewServiceClient(
        base_url=state['review_service_base_url'],
        llm_config=state['llm_config']
    )
    diff = mcp_client.get_pr_diff(state['pr_url'])
    review_body = review_service.perform_code_review(diff, "Perform a critical code review.")
    logger.info("Code review completed.")
    return {**state, "review_results": review_body}

def doc_review_node(state: AgentState) -> AgentState:
    logger.info(f"Performing documentation review for PR: {state['pr_url']}")
    review_service = ReviewServiceClient(
        base_url=state['review_service_base_url'],
        llm_config=state['llm_config']
    )
    diff = mcp_client.get_pr_diff(state['pr_url'])
    doc_review_result = review_service.perform_doc_review(diff, "Review the documentation changes.")
    logger.info("Documentation review completed.")
    return {**state, "doc_review_results": doc_review_result.get("review", "Documentation Review Failed.")}

def prepare_repo(state: AgentState) -> AgentState:
    logger.info(f"Preparing repository from {state['repo_src']}")
    
    artifacts_dir = new_task_dir()
    repo_dir = artifacts_dir / "repo"
    
    clone_or_copy(state['repo_src'], repo_dir, state['branch'])
    summary = summarize_repo(repo_dir)
    
    languages = state['languages']
    if not languages:
        languages = detect_languages(repo_dir)
        logger.info(f"No languages specified, auto-detected: {languages}")
    else:
        autod = detect_languages(repo_dir)
        initial_languages = languages
        languages = [l for l in languages if l in autod]
        logger.info(f"Intersected requested languages {initial_languages} with auto-detected {autod}. Final languages: {languages}")

    return {
        **state,
        "artifacts_dir": artifacts_dir,
        "repo_dir": repo_dir,
        "summary": summary,
        "languages": languages,
    }

def generate_tests_node(state: AgentState) -> AgentState:
    logger.info("Planning test targets via Review Service.")
    review_service = ReviewServiceClient(
        base_url=state['review_service_base_url'], 
        llm_config=state['llm_config']
    )
    targets = review_service.plan_test_targets(state['summary'], state['languages'])
    logger.info(f"Test targets planned: {targets}")
    generated = {}
    for lang, files in targets.items():
        generated[lang] = []
        for relpath in files:
            logger.info(f"Generating tests for {relpath} in {lang} via Review Service")
            spec = review_service.generate_tests(lang, relpath, str(state['repo_dir']))
            out_path = state['repo_dir'] / spec["test_path"]
            write_file(out_path, spec["content"])
            generated[lang].append({"file": relpath, "test_path": spec["test_path"]})
            logger.info(f'Generated test for {relpath}: {spec["test_path"]}')
    return {**state, "generated_tests": generated}

def static_checks_node(state: AgentState) -> AgentState:
    logger.info("Running static checks via Review and Pentest Services.")
    review_service = ReviewServiceClient(
        base_url=state['review_service_base_url'], 
        llm_config=state['llm_config']
    )
    pentest_service = PentestServiceClient(
        base_url=state['pentest_service_base_url'], 
        llm_config=state['llm_config']
    )
    results = {}
    for lang in state['languages']:
        logger.info(f"Running static review for language: {lang} via Review Service")
        review_results = review_service.static_review(lang, str(state['repo_dir']))
        logger.info(f"Running static pentest for language: {lang} via Pentest Service")
        pentest_results = pentest_service.static_pentest(lang, str(state['repo_dir']))
        results[lang] = {"review": review_results, "pentest": pentest_results}
        logger.info(f"Static analysis for {lang} completed.")
    return {**state, "static_results": results}

def run_tests_node(state: AgentState) -> AgentState:
    logger.info("Running generated tests and collecting artifacts.")
    outputs = {}
    coverage_data = {}
    for lang in state['languages']:
        logger.info(f"Running tests for language: {lang}")
        code, out, files = run_in_container(lang, state['repo_dir'])
        outputs[lang] = {"exit_code": code, "output": out}
        logger.info(f"Tests for {lang} completed with exit code {code}.")
        
        if lang == "python" and "coverage.xml" in files:
            logger.info("Python coverage.xml artifact found. Parsing...")
            coverage_data["python"] = parse_python_coverage_xml(files["coverage.xml"])
            logger.info(f"Python overall coverage: {coverage_data['python'].get('overall_coverage', 'N/A')}")
            
    return {**state, "test_results": outputs, "coverage_results": coverage_data}

def report_node(state: AgentState) -> AgentState:
    logger.info("Generating report.")
    blocks = [
        {"title": "Repo Summary", "meta": str(state['summary']), "output": None},
        {"title": "Generated Tests", "meta": str(state['generated_tests']), "output": None},
    ]
    
    if state['static_results']:
        for lang, s_res in state['static_results'].items():
            if "review" in s_res:
                blocks.append({"title": f"Static Review ({lang})", "meta": None, "output": str(s_res["review"])})
            if "pentest" in s_res:
                blocks.append({"title": f"Static Pentest ({lang})", "meta": None, "output": str(s_res["pentest"])})
    
    if state['test_results']:
        for lang, r in state['test_results'].items():
            blocks.append({"title": f"Test Run ({lang})", "meta": f"exit={r['exit_code']}", "output": r["output"]})
    
    if state['dynamic_pentest_results']:
        for lang, res in state['dynamic_pentest_results'].items():
            blocks.append({"title": f"Dynamic Pentest ({lang})", "meta": None, "output": str(res)})
            
    report_path = write_report(state['artifacts_dir'], state['languages'], state['summary'], blocks)
    logger.info(f"Report generated at: {report_path}")
    return {**state, "report_path": report_path}

def router_node(state: AgentState, llm: BaseChatModel) -> AgentState:
    """
    This node uses an LLM to decide the next step based on the current AgentState.
    It updates the 'next_step' field in the state.
    """
    
    # Determine possible next steps based on current state
    possible_steps = ["end"]
    if state.get("repo_src") and not state.get("summary"):
        possible_steps.append("prepare_repo")
    if state.get("pr_url") and not state.get("review_results"):
        possible_steps.extend(["code_review", "doc_review"])
    if state.get("summary") and not state.get("generated_tests"):
        possible_steps.append("generate_tests")
    if state.get("summary") and not state.get("static_results"):
        possible_steps.append("static_checks")
    if state.get("generated_tests") and not state.get("test_results"):
        possible_steps.append("run_tests")
    if state.get("test_results") and not state.get("dynamic_pentest_results"):
        possible_steps.append("dynamic_pentest")
    if state.get("test_results") or state.get("static_results") or state.get("review_results") or state.get("dynamic_pentest_results"):
        if "report" not in possible_steps:
            possible_steps.append("report")

    # Filter out 'end' if there are other possible steps
    if len(possible_steps) > 1 and "end" in possible_steps:
        possible_steps.remove("end")

    logger.info(f"Possible next steps: {possible_steps}")

    if not possible_steps or len(possible_steps) == 1 and possible_steps[0] == "end":
        next_step = "end"
    elif len(possible_steps) == 1:
        next_step = possible_steps[0]
    else:
        prompt_template = f"""You are an expert in code analysis workflows. Your task is to decide the next step in the workflow.
Given the current state of the analysis:

{{state}}

Choose the next step from the following options: {', '.join(possible_steps)}

Respond with only one word from the list of options."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            ("human", "Current state: {state}")
        ])
        
        chain = prompt | llm
        
        response = chain.invoke({"state": state})
        next_step = response.content.strip().lower()
        logger.info(f"LLM chose next step: {next_step}")

    if next_step not in possible_steps:
        logger.warning(f"LLM returned an invalid next step: '{next_step}'. Defaulting to 'end'.")
        next_step = "end"
        
    return {**state, "next_step": next_step}

def build_graph(llm: BaseChatModel) -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("prepare_repo", prepare_repo)
    workflow.add_node("code_review", code_review_node)
    workflow.add_node("doc_review", doc_review_node)
    workflow.add_node("generate_tests", generate_tests_node)
    workflow.add_node("static_checks", static_checks_node)
    workflow.add_node("run_tests", run_tests_node)
    workflow.add_node("dynamic_pentest", dynamic_pentest_node)
    workflow.add_node("report", report_node)
    workflow.add_node("router", lambda state: router_node(state, llm))

    workflow.set_entry_point("router")

    workflow.add_edge("prepare_repo", "router")
    workflow.add_edge("code_review", "router")
    workflow.add_edge("doc_review", "router")
    workflow.add_edge("generate_tests", "router")
    workflow.add_edge("static_checks", "router")
    workflow.add_edge("run_tests", "router")
    workflow.add_edge("dynamic_pentest", "router")
    workflow.add_edge("report", "router")

    workflow.add_conditional_edges(
        "router",
        lambda state: state["next_step"], 
        {
            "prepare_repo": "prepare_repo",
            "code_review": "code_review",
            "doc_review": "doc_review",
            "generate_tests": "generate_tests",
            "static_checks": "static_checks",
            "run_tests": "run_tests",
            "dynamic_pentest": "dynamic_pentest",
            "report": "report",
            "end": "__end__",
        },
    )

    return workflow.compile()
