import os
import json
import subprocess
import streamlit as st

st.set_page_config(page_title="PentestAI UI", layout="wide")
st.title("PentestAI — Reports & Runner")

st.sidebar.header("Runner")
git_url = st.sidebar.text_input("Git URL", value="[https://github.com/virattt/dexter.git](https://github.com/virattt/dexter.git)")
branch = st.sidebar.text_input("Branch (optional)", value="")
out_dir = st.sidebar.text_input("Output dir", value="artifacts_ui")
run_clicked = st.sidebar.button("Run analysis")

if run_clicked:
    st.sidebar.write("Running…")
    cmd = ["python", "-m", "pentestai.main", "--git", git_url, "--out", out_dir]
    if branch.strip():
        cmd += ["--branch", branch.strip()]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        with st.status("Executing pipeline…", expanded=True) as status:
            for line in proc.stdout:
                st.write(line.rstrip())
            rc = proc.wait()
            status.update(label=f"Run complete (exit {rc})", state="complete" if rc==0 else "error")
    except Exception as e:
        st.sidebar.error(f"Failed: {e}")

st.header("Existing Reports")
cands = []
for root, dirs, files in os.walk("."):
    if "report.json" in files:
        cands.append(os.path.join(root, "report.json"))
cands = sorted(cands)
if not cands:
    st.info("No report.json found yet. Run the pipeline from the sidebar.")
else:
    choice = st.selectbox("Select report.json", options=cands, index=len(cands)-1)
    with open(choice, "r", encoding="utf-8") as f:
        report = json.load(f)
    st.subheader("Summary")
    st.json(report.get("summary", {}))
    st.subheader("Sections")
    for section in report.get("sections", []):
        with st.expander(section.get("persona","(unknown)")):
            st.json(section)
    st.subheader("Metadata")
    st.json(report.get("metadata", {}))
