import os, time, httpx, streamlit as st
from pathlib import Path

st.set_page_config(page_title="AI Agent Test Orchestrator", layout="wide")
st.title("🧪 AI Agent: Code Understanding & Test Runner")

# Initialize session state for settings if not already present
if 'settings' not in st.session_state:
    st.session_state.settings = {
        "API_BASE_URL": os.getenv("API_BASE_URL", "http://0.0.0.0:8000"),
        "REVIEW_SERVICE_BASE_URL": os.getenv("REVIEW_SERVICE_BASE_URL", "http://review_service:8000"),
        "PENTEST_SERVICE_BASE_URL": os.getenv("PENTEST_SERVICE_BASE_URL", "http://pentest_service:8000"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "LLM_TEMPERATURE": float(os.getenv("LLM_TEMPERATURE", 0.2)),
        "LLM_MAX_TOKENS_REVIEW": int(os.getenv("LLM_MAX_TOKENS_REVIEW", 4000)),
        "LLM_MAX_TOKENS_TESTGEN": int(os.getenv("LLM_MAX_TOKENS_TESTGEN", 1200)),
        "LLM_MAX_TOKENS_DOC_REVIEW": int(os.getenv("LLM_MAX_TOKENS_DOC_REVIEW", 2000)),
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "openai"), # Default to openai
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY", ""),
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        "AZURE_OPENAI_DEPLOYMENT_NAME": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", ""),
    }

tab1, tab2, tab3 = st.tabs(["Analyze & Test", "Code Review & Compare", "Settings"])

with tab1:
    repo_url = st.text_input("Git repo URL (public or with access) OR leave blank to use mounted path:")
    upload_dir = st.text_input("Mounted local path inside API container (e.g., /data/project)")
    branch = st.text_input("Branch (optional, defaults to the repository's default branch)")
    languages = st.multiselect("Languages", ["python","node","java"], default=["python","node","java"])

    if st.button("Analyze & Test", type="primary"):
        if not (repo_url or upload_dir):
            st.error("Provide a repo_url or upload_dir")
        else:
            with st.spinner("Starting task..."):
                # Prepare LLM config to send to the backend
                llm_config = {
                    "llm_provider": st.session_state.settings["LLM_PROVIDER"],
                    "llm_temperature": st.session_state.settings["LLM_TEMPERATURE"],
                    "llm_max_tokens_review": st.session_state.settings["LLM_MAX_TOKENS_REVIEW"],
                    "llm_max_tokens_testgen": st.session_state.settings["LLM_MAX_TOKENS_TESTGEN"],
                    "llm_max_tokens_doc_review": st.session_state.settings["LLM_MAX_TOKENS_DOC_REVIEW"],
                }
                if st.session_state.settings["LLM_PROVIDER"] == "openai":
                    llm_config["openai_api_key"] = st.session_state.settings["OPENAI_API_KEY"]
                    llm_config["openai_model"] = st.session_state.settings["OPENAI_MODEL"]
                elif st.session_state.settings["LLM_PROVIDER"] == "azure":
                    llm_config["azure_openai_api_key"] = st.session_state.settings["AZURE_OPENAI_API_KEY"]
                    llm_config["azure_openai_endpoint"] = st.session_state.settings["AZURE_OPENAI_ENDPOINT"]
                    llm_config["azure_openai_deployment_name"] = st.session_state.settings["AZURE_OPENAI_DEPLOYMENT_NAME"]

                r = httpx.post(
                    f"{st.session_state.settings['API_BASE_URL']}/analyze",
                    json={
                        "repo_url": repo_url or None,
                        "upload_dir": upload_dir or None,
                        "branch": branch or None,
                        "languages": languages,
                        "llm_config": llm_config, # Pass LLM config
                        "review_service_base_url": st.session_state.settings["REVIEW_SERVICE_BASE_URL"], # Pass service URLs
                        "pentest_service_base_url": st.session_state.settings["PENTEST_SERVICE_BASE_URL"],
                    }
                )
                r.raise_for_status()
                tid = r.json()["task_id"]
                st.session_state["tid"] = tid

with tab2:
    review_type = st.radio("Review Type", ["Pull Request", "Branch Comparison"])

    if review_type == "Pull Request":
        pr_url = st.text_input("GitHub PR URL")
        prompt = st.text_area("Custom Prompt (optional)", placeholder="e.g., Focus on security vulnerabilities and performance issues.")

        llm_config = {
            "llm_provider": st.session_state.settings["LLM_PROVIDER"],
            "llm_temperature": st.session_state.settings["LLM_TEMPERATURE"],
            "llm_max_tokens_review": st.session_state.settings["LLM_MAX_TOKENS_REVIEW"],
            "llm_max_tokens_testgen": st.session_state.settings["LLM_MAX_TOKENS_TESTGEN"],
            "llm_max_tokens_doc_review": st.session_state.settings["LLM_MAX_TOKENS_DOC_REVIEW"],
        }
        if st.session_state.settings["LLM_PROVIDER"] == "openai":
            llm_config["openai_api_key"] = st.session_state.settings["OPENAI_API_KEY"]
            llm_config["openai_model"] = st.session_state.settings["OPENAI_MODEL"]
        elif st.session_state.settings["LLM_PROVIDER"] == "azure":
            llm_config["azure_openai_api_key"] = st.session_state.settings["AZURE_OPENAI_API_KEY"]
            llm_config["azure_openai_endpoint"] = st.session_state.settings["AZURE_OPENAI_ENDPOINT"]
            llm_config["azure_openai_deployment_name"] = st.session_state.settings["AZURE_OPENAI_DEPLOYMENT_NAME"]
        r = httpx.post(
            f"{st.session_state.settings['API_BASE_URL']}/code-review",
            json={
                "pr_url": pr_url,
                "prompt": prompt,
                "llm_config": llm_config,
                "review_service_base_url": st.session_state.settings["REVIEW_SERVICE_BASE_URL"],
                "pentest_service_base_url": st.session_state.settings["PENTEST_SERVICE_BASE_URL"],
            }
        )
        r.raise_for_status()
        tid = r.json()["task_id"]
        st.session_state["tid"] = tid
    
    elif review_type == "Branch Comparison":
        repo_url_compare = st.text_input("Git repo URL")
        col1, col2 = st.columns(2)
        with col1:
            base_branch = st.text_input("Base branch")
        with col2:
            head_branch = st.text_input("Head branch")
        
        if st.button("Get Branches"):
            if not repo_url_compare:
                st.error("Provide a repo URL to get branches")
            else:
                with st.spinner("Fetching branches..."):
                    try:
                        r = httpx.post(f"{st.session_state.settings['API_BASE_URL']}/repository/branches", json={"repo_url": repo_url_compare})
                        r.raise_for_status()
                        st.session_state['branches'] = r.json()
                    except httpx.HTTPStatusError as e:
                        st.error(f"Error fetching branches: {e.response.text}")
        
        if 'branches' in st.session_state:
            st.write("**Available Branches:**")
            st.write(st.session_state['branches'])

        prompt_compare = st.text_area("Custom Prompt (optional)", placeholder="e.g., Focus on security vulnerabilities and performance issues.", key="prompt_compare")

        if st.button("Start Comparison", type="primary"):
            if not all([repo_url_compare, base_branch, head_branch]):
                st.error("Provide a repo URL, base branch, and head branch")
            else:
                with st.spinner("Starting task..."):
                    llm_config = {
                        "openai_api_key": st.session_state.settings["OPENAI_API_KEY"],
                        "openai_model": st.session_state.settings["OPENAI_MODEL"],
                        "llm_temperature": st.session_state.settings["LLM_TEMPERATURE"],
                        "llm_max_tokens_review": st.session_state.settings["LLM_MAX_TOKENS_REVIEW"],
                        "llm_max_tokens_testgen": st.session_state.settings["LLM_MAX_TOKENS_TESTGEN"],
                        "llm_max_tokens_doc_review": st.session_state.settings["LLM_MAX_TOKENS_DOC_REVIEW"],
                    }
                    r = httpx.post(
                        f"{st.session_state.settings['API_BASE_URL']}/repository/compare",
                        json={
                            "repo_url": repo_url_compare, 
                            "base": base_branch, 
                            "head": head_branch, 
                            "prompt": prompt_compare,
                            "llm_config": llm_config,
                            "review_service_base_url": st.session_state.settings["REVIEW_SERVICE_BASE_URL"],
                            "pentest_service_base_url": st.session_state.settings["PENTEST_SERVICE_BASE_URL"],
                        }
                    )
                    r.raise_for_status()
                    tid = r.json()["task_id"]
                    st.session_state["tid"] = tid

with tab3:
    st.header("Service Endpoints")
    st.session_state.settings["API_BASE_URL"] = st.text_input(
        "Orchestration Service Base URL",
        st.session_state.settings["API_BASE_URL"],
        key="api_base_url_input"
    )
    st.session_state.settings["REVIEW_SERVICE_BASE_URL"] = st.text_input(
        "Review Service Base URL",
        st.session_state.settings["REVIEW_SERVICE_BASE_URL"],
        key="review_service_base_url_input"
    )
    st.session_state.settings["PENTEST_SERVICE_BASE_URL"] = st.text_input(
        "Pentest Service Base URL",
        st.session_state.settings["PENTEST_SERVICE_BASE_URL"],
        key="pentest_service_base_url_input"
    )

    st.header("LLM Configuration")
    st.session_state.settings["LLM_PROVIDER"] = st.radio(
        "LLM Provider",
        ("openai", "azure"),
        index=0 if st.session_state.settings["LLM_PROVIDER"] == "openai" else 1,
        key="llm_provider_input"
    )

    if st.session_state.settings["LLM_PROVIDER"] == "openai":
        st.session_state.settings["OPENAI_API_KEY"] = st.text_input(
            "OpenAI API Key",
            st.session_state.settings["OPENAI_API_KEY"],
            type="password",
            key="openai_api_key_input"
        )
        st.session_state.settings["OPENAI_MODEL"] = st.text_input(
            "OpenAI Model",
            st.session_state.settings["OPENAI_MODEL"],
            key="openai_model_input"
        )
    elif st.session_state.settings["LLM_PROVIDER"] == "azure":
        st.session_state.settings["AZURE_OPENAI_API_KEY"] = st.text_input(
            "Azure OpenAI API Key",
            st.session_state.settings["AZURE_OPENAI_API_KEY"],
            type="password",
            key="azure_openai_api_key_input"
        )
        st.session_state.settings["AZURE_OPENAI_ENDPOINT"] = st.text_input(
            "Azure OpenAI Endpoint",
            st.session_state.settings["AZURE_OPENAI_ENDPOINT"],
            key="azure_openai_endpoint_input"
        )
        st.session_state.settings["AZURE_OPENAI_DEPLOYMENT_NAME"] = st.text_input(
            "Azure OpenAI Deployment Name",
            st.session_state.settings["AZURE_OPENAI_DEPLOYMENT_NAME"],
            key="azure_openai_deployment_name_input"
        )

    st.session_state.settings["LLM_TEMPERATURE"] = st.number_input(
        "LLM Temperature",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.settings["LLM_TEMPERATURE"],
        step=0.01,
        key="llm_temperature_input"
    )
    st.session_state.settings["LLM_MAX_TOKENS_REVIEW"] = st.number_input(
        "LLM Max Tokens (Code Review)",
        min_value=500,
        value=st.session_state.settings["LLM_MAX_TOKENS_REVIEW"],
        step=100,
        key="llm_max_tokens_review_input"
    )
    st.session_state.settings["LLM_MAX_TOKENS_TESTGEN"] = st.number_input(
        "LLM Max Tokens (Test Generation)",
        min_value=100,
        value=st.session_state.settings["LLM_MAX_TOKENS_TESTGEN"],
        step=50,
        key="llm_max_tokens_testgen_input"
    )
    st.session_state.settings["LLM_MAX_TOKENS_DOC_REVIEW"] = st.number_input(
        "LLM Max Tokens (Doc Review)",
        min_value=100,
        value=st.session_state.settings["LLM_MAX_TOKENS_DOC_REVIEW"],
        step=50,
        key="llm_max_tokens_doc_review_input"
    )

def display_download_buttons(tid, report_path_full, api_base_url):
    """Handles fetching and displaying download buttons for various report types."""
    
    st.markdown(f"**Report Path:** `{report_path_full}` (Check your host volume)")
    
    try:
        path_obj = Path(report_path_full)
        filename = path_obj.name
        
        files_to_download = []
        if filename in ["report.html", "report.md"]:
            # For the Analysis task, offer both HTML and MD versions
            files_to_download.append(("report.html", "text/html", "Full HTML Report"))
            files_to_download.append(("report.md", "text/markdown", "Summary Markdown Report"))
        else:
            # For the Code Review/Compare task, offer the single MD file
            files_to_download.append((filename, "text/markdown", "Markdown Review Report"))

        for download_filename, mime_type, button_label in files_to_download:
            download_url = f"{api_base_url}/artifacts/{tid}/{download_filename}"
            
            # Fetch content for st.download_button
            report_content_resp = httpx.get(download_url, timeout=30)
            report_content_resp.raise_for_status()
            report_content = report_content_resp.content
            
            # Display the download button
            st.download_button(
                label=f"Download {button_label}",
                data=report_content,
                file_name=download_filename,
                mime=mime_type,
                key=f"download_{download_filename}"
            )

    except httpx.HTTPStatusError as e:
        st.error(f"Could not fetch report content for download. Check API logs. Error: {e.response.text}")
    except Exception as e:
        st.warning(f"Using fallback link due to unexpected error: {e}")
        st.markdown(f"**Report Fallback:** `{report_path_full}` (open on host volume)") # Fallback


if tid := st.session_state.get("tid"):
    st.info(f"Task ID: {tid}")
    ph = st.empty()
    while True:
        s = httpx.get(f"{st.session_state.settings['API_BASE_URL']}/status/{tid}").json()
        if s["status"] in ("queued","running"):
            ph.write(f"Status: **{s['status']}** ...")
            time.sleep(2)
        elif s["status"] == "done":
            ph.success("Done!")
            
            report_path_full = s["report_path"]
            
            # Logic to handle review posting vs. report file download
            if report_path_full.startswith("Review posted to PR:"):
                 st.markdown(f"**Result:** {report_path_full}")
            else:
                # REPLACED OLD LOGIC: Use the new helper function for download buttons
                display_download_buttons(tid, report_path_full, st.session_state.settings["API_BASE_URL"])
            
            st.stop()
        else:
            ph.error(f"Error: {s.get('error')}")
            st.stop()

 
