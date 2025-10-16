from pathlib import Path
from jinja2 import Template
from datetime import datetime

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
