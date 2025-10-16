import os, time, httpx, streamlit as st
from pathlib import Path
API = os.getenv("API_BASE_URL", "http://0.0.0.0:8000")

st.set_page_config(page_title="AI Agent Test Orchestrator", layout="wide")
st.title("🧪 AI Agent: Code Understanding & Test Runner")

tab1, tab2 = st.tabs(["Analyze & Test", "Code Review & Compare"])

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
                r = httpx.post(f"{API}/analyze", json={"repo_url": repo_url or None, "upload_dir": upload_dir or None, "branch": branch or None, "languages": languages})
                r.raise_for_status()
                tid = r.json()["task_id"]
                st.session_state["tid"] = tid

with tab2:
    review_type = st.radio("Review Type", ["Pull Request", "Branch Comparison"])

    if review_type == "Pull Request":
        pr_url = st.text_input("GitHub PR URL")
        prompt = st.text_area("Custom Prompt (optional)", placeholder="e.g., Focus on security vulnerabilities and performance issues.")

        if st.button("Start Code Review", type="primary"):
            if not pr_url:
                st.error("Provide a GitHub PR URL")
            else:
                with st.spinner("Starting task..."):
                    r = httpx.post(f"{API}/code-review", json={"pr_url": pr_url, "prompt": prompt})
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
                        r = httpx.post(f"{API}/repository/branches", json={"repo_url": repo_url_compare})
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
                    r = httpx.post(f"{API}/repository/compare", json={
                        "repo_url": repo_url_compare, 
                        "base": base_branch, 
                        "head": head_branch, 
                        "prompt": prompt_compare
                    })
                    r.raise_for_status()
                    tid = r.json()["task_id"]
                    st.session_state["tid"] = tid

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
        s = httpx.get(f"{API}/status/{tid}").json()
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
                display_download_buttons(tid, report_path_full, API)
            
            st.stop()
        else:
            ph.error(f"Error: {s.get('error')}")
            st.stop()