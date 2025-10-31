#!/usr/bin/env bash  
set -euo pipefail  
OUT_DIR=${1:-artifacts_dexter}  
python -m pentestai.main --git [https://github.com/virattt/dexter.git](https://github.com/virattt/dexter.git) --out "$OUT_DIR"  
echo "Report -> $OUT_DIR/report.html ; $OUT_DIR/report.json"  
EOF  
chmod +x "$ROOT/scripts/run_dexter.sh"

# -------------------- profiles --------------------

cat > "$ROOT/profiles/python_default.yaml" << 'EOF'  
static:  
tools: [bandit, semgrep, eslint]  
tests:  
tools: [pytest]  
dynamic:  
tools: []  
