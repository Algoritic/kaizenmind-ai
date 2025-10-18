from pathlib import Path
from jinja2 import Template
from datetime import datetime
import xml.etree.ElementTree as ET # NEW: For parsing coverage XML
from typing import Dict # NEW: For type hinting

HTML_TEMPLATE = Template(
    """
    <html><head><meta charset="utf-8"><title>Agent Report</title>
    <style>body{font-family:Inter,system-ui,Arial;margin:24px;}
    .card{border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:16px 0;}
    pre{background:#0b1020;color:#d1d5db;padding:12px;border-radius:8px;overflow:auto;}
    code{font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace;}
    h1,h2{margin:8px 0}
    table{border-collapse:collapse;width:100%}
    td,th{border:1px solid #e5e7eb;padding:8px;text-align:left}
    .ok{color:#059669}.fail{color:#dc2626}
    </style></head>
    <body>
    <h1>AI Agent Test Report</h1>
    <p>Generated: {{ ts }}</p>
    <div class="card"><h2>Summary</h2>
    <table>
      <tr><th>Files</th><td>{{ summary.file_count }}</td></tr>
      <tr><th>Languages</th><td>{{ languages|join(', ') }}</td></tr>
      <tr><th>Has existing tests</th><td>{{ 'Yes' if summary.has_tests else 'No' }}</td></tr>
    </table></div>

    {% for block in blocks %}
      <div class="card">
        <h2>{{ block.title }}</h2>
        {% if block.meta %}<pre><code>{{ block.meta }}</code></pre>{% endif %}
        {% if block.output %}<pre><code>{{ block.output }}</code></pre>{% endif %}
      </div>
    {% endfor %}

    </body></html>
    """
)


def write_report(artifacts_dir: Path, languages, summary, blocks):
    html = HTML_TEMPLATE.render(ts=datetime.utcnow().isoformat(), languages=languages, summary=summary, blocks=blocks)
    out_html = artifacts_dir / "report.html"
    out_md = artifacts_dir / "report.md"
    out_html.write_text(html, encoding='utf-8')
    # Brief Markdown companion
    out_md.write_text(f"# AI Agent Report\n\nLanguages: {', '.join(languages)}\n\nFiles: {summary['file_count']}\n\nSee detailed HTML.\n", encoding='utf-8')
    return str(out_html)

# Report writer for code reviews
def write_review_report(artifacts_dir: Path, review_body: str, file_name: str) -> str:
    """Writes a Markdown review body to a file and returns the absolute path."""
    out_md = artifacts_dir / file_name
    out_md.write_text(review_body, encoding='utf-8')
    return str(out_md)

# NEW FUNCTION: Tool to parse coverage data for the LLM review
def parse_python_coverage_xml(xml_content: bytes) -> Dict:
    """Parses a Python coverage.xml file and returns a summary dict."""
    try:
        root = ET.fromstring(xml_content.decode('utf-8'))
        
        totals = root.find('packages/package/metrics') # Adjusted path for common coverage XML output
        if totals is None:
            totals = root.find('project/metrics') # Fallback path
            if totals is None:
                 return {"overall_coverage": "N/A", "covered_lines": 0, "missed_lines": 0, "error": "No coverage metrics found."}
            
        covered = int(totals.get('covered_statements', '0'))
        missed = int(totals.get('missed_statements', '0'))
        lines = covered + missed
        coverage_percent = (covered / lines) * 100 if lines > 0 else 0
        
        # Extract file-level details for added context (up to 5 files)
        file_details = []
        # Adjusted path for common coverage XML output
        for file in root.findall('.//file')[:5]:
            file_lines = int(file.get('statements', '0'))
            file_missed = int(file.get('missing-statements', '0'))
            file_coverage = (file_lines - file_missed) / file_lines * 100 if file_lines > 0 else 0

            file_details.append({
                "name": file.get('name'),
                "coverage": f"{file_coverage:.2f}%",
                "lines": file_lines,
                "missed": file_missed
            })

        return {
            "overall_coverage": f"{coverage_percent:.2f}%",
            "covered_lines": covered,
            "missed_lines": missed,
            "total_lines": lines,
            "file_details": file_details,
            "error": None
        }
    except ET.ParseError:
        return {"overall_coverage": "N/A", "error": "Failed to parse coverage XML."}
    except Exception as e:
        return {"overall_coverage": "N/A", "error": f"Unexpected error during coverage parsing: {e}"}