# Langraph Refactoring Specification for AI Agent Unit Test and Review Product

## Objective

The primary objective of this refactoring effort was to transform the existing `ai-agent-unit-test-and-review` product's orchestration service to utilize the `langraph` framework. This aims to build a more dynamic and intelligent agent capable of reasoning, handling complex tasks, and devising better testing strategies, moving away from static, predefined steps.

## Phases and Changes

### Phase 1: Setup Langraph Environment

**1. `orchestration_service/requirements.txt` Modification**

*   **Change:** Added `langraph` to the list of dependencies.
*   **Reason:** To enable the use of the `langraph` framework for building the new dynamic agent.

**2. `orchestration_service/app/langraph_agent.py` Creation**

*   **Change:** Created a new Python file `langraph_agent.py`.
*   **Reason:** This file will house the `langraph` specific implementation, including the `AgentState` definition, individual graph nodes (refactored `Orchestrator` methods), and the `langraph` workflow construction.

### Phase 2: Define Graph State

**1. `orchestration_service/app/langraph_agent.py` - `AgentState` Definition**

*   **Change:** Defined a `TypedDict` named `AgentState` to represent the state of the agent throughout the analysis process.
*   **Reason:** `langraph` workflows operate by passing a state object between nodes. This `AgentState` consolidates all relevant information (e.g., repository details, LLM configuration, analysis results) that was previously managed by the `Orchestrator` class's instance variables.

### Phase 3: Convert Orchestrator Methods to Graph Nodes/Tools

**1. `orchestration_service/app/langraph_agent.py` - `prepare_repo` Function**

*   **Change:** Refactored the `prepare` method from the original `Orchestrator` class into a standalone function `prepare_repo`.
*   **Reason:** Each significant step in the `Orchestrator`'s workflow needs to become a distinct, callable node in the `langraph` graph. This function now takes `AgentState` as input, performs repository preparation (cloning/copying, summarizing), and returns an updated `AgentState`.

**2. `orchestration_service/app/langraph_agent.py` - `generate_tests_node` Function**

*   **Change:** Refactored the `generate_tests` method from `Orchestrator` into `generate_tests_node`.
*   **Reason:** To encapsulate the test generation logic as a `langraph` node. It instantiates `ReviewServiceClient` using information from `AgentState`, plans and generates tests, writes them to the repository, and updates the `AgentState` with the generated test details.

**3. `orchestration_service/app/langraph_agent.py` - `static_checks_node` Function**

*   **Change:** Refactored the `static_checks` method from `Orchestrator` into `static_checks_node`.
*   **Reason:** To create a `langraph` node for performing static analysis. It instantiates `ReviewServiceClient` and `PentestServiceClient`, runs static reviews and pentests for detected languages, and updates `AgentState` with the results.

**4. `orchestration_service/app/langraph_agent.py` - `run_tests_node` Function**

*   **Change:** Refactored the `run_tests` method from `Orchestrator` into `run_tests_node`.
*   **Reason:** To create a `langraph` node responsible for executing generated tests. It uses `run_in_container` to run tests, parses Python coverage data if available, and updates `AgentState` with test outputs and coverage results.

**5. `orchestration_service/app/langraph_agent.py` - `report_node` Function**

*   **Change:** Refactored the `report` method and report generation logic from `Orchestrator.run_all` into `report_node`.
*   **Reason:** To create a `langraph` node for generating the final analysis report. It constructs report blocks from the various results stored in `AgentState` and updates the state with the path to the generated report.

### Phase 4 & 5: Implement Dynamic Agent Logic and Build Graph

**1. `orchestration_service/app/langraph_agent.py` - Imports and `router_node` Function**

*   **Change:** Added imports for `Graph`, `StateGraph` from `langgraph`, `ChatOpenAI`, `BaseChatModel`, `ChatPromptTemplate`, `RunnablePassthrough` from `langchain_core`. Introduced a new function `router_node`.
*   **Reason:** To enable dynamic decision-making within the workflow. The `router_node` uses an LLM (e.g., `ChatOpenAI`) to analyze the current `AgentState` and determine the most appropriate next step (e.g., `generate_tests`, `static_checks`, `run_tests`, `report`, or `end`). This replaces the fixed sequential execution with an intelligent routing mechanism.

**2. `orchestration_service/app/langraph_agent.py` - `build_graph` Function**

*   **Change:** Modified the `build_graph` function to construct the `langraph` workflow.
*   **Reason:** This function now defines the nodes (`prepare_repo`, `generate_tests_node`, `static_checks_node`, `run_tests_node`, `report_node`, `router`) and the edges between them. Crucially, it uses `add_conditional_edges` with the `router_node` to allow the LLM to dictate the flow of execution, making the agent dynamic.

**3. `orchestration_service/app/langraph_agent.py` - `AgentState` `next_step` field**

*   **Change:** Added `next_step: str` to `AgentState` and removed `next_step` assignments from individual node functions.
*   **Reason:** The `router_node` is now solely responsible for setting the `next_step` in the `AgentState` based on the LLM's decision. This centralizes the control flow logic.

### Phase 6: Update FastAPI Integration

**1. `orchestration_service/app/main.py` - Imports**

*   **Change:** Removed `from app.agent import Orchestrator, ReviewServiceClient`. Added `from app.langraph_agent import build_graph, AgentState` and `from langchain_openai import ChatOpenAI`.
*   **Reason:** To switch from the old `Orchestrator`-based system to the new `langraph` workflow. The `ReviewServiceClient` import was removed from the global scope as it's now instantiated within the `langraph` nodes when needed.

**2. `orchestration_service/app/main.py` - LLM and Workflow Initialization**

*   **Change:** Initialized `llm = ChatOpenAI(...)` and `workflow = build_graph(llm)` globally in `main.py`.
*   **Reason:** To create a single instance of the LLM and the `langraph` workflow that can be reused across requests, improving efficiency and consistency.

**3. `orchestration_service/app/main.py` - `_run_task` Function Modification**

*   **Change:** The `_run_task` function was significantly altered:
    *   Removed `Orchestrator` instantiation and `orch.run_all()` call.
    *   Constructed an initial `AgentState` dictionary from the `AnalyzeRequest`.
    *   Invoked the `langraph` `workflow` with this initial state.
    *   Extracted the final `report_path` from the `workflow.invoke()` result.
*   **Reason:** This is the core change that integrates the `langraph` dynamic agent. Instead of a fixed sequence, the `_run_task` now delegates the entire analysis process to the `langraph` workflow, allowing the LLM-powered router to determine the optimal path through the analysis steps.

**4. `orchestration_service/app/main.py` - `analyze` Endpoint Update**

*   **Change:** The `Thread(target=_run_task, args=(tid, req), daemon=True).start()` call remains, but `_run_task` now operates on the `langraph` workflow.
*   **Reason:** To ensure that new analysis requests correctly trigger the `langraph`-based dynamic agent.

## Future Considerations

*   **Error Handling:** Enhance error handling within `langraph` nodes and the router to gracefully manage failures and potentially retry or choose alternative paths.
*   **Tool Definition:** Formalize the `ReviewServiceClient` and `PentestServiceClient` methods as `langchain` tools for better integration with the LLM's tool-use capabilities.
*   **Dynamic Prompting:** Refine the LLM prompt in `router_node` to provide more context or allow for more nuanced decision-making based on the `AgentState`.
*   **Observability:** Integrate `langsmith` or similar tools for better tracing and debugging of the `langraph` workflow.
