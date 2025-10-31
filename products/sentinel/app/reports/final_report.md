# Security AI — Hybrid Review Report
**Run ID:** run-sample
**Generated:** 2025-10-29T09:03:00.898627Z

## Summary

| critical | high | medium | low |
|---------:|-----:|-------:|----:|
| 0 | 10 | 20 | 10 |

<details><summary>Summary JSON</summary>

```json
{
  "critical": 0,
  "high": 10,
  "medium": 20,
  "low": 10
}
```
</details>

## Ranked Findings
- **[high]** Secret-scan heuristic
- **[high]** API deep fuzzing
- **[medium]** Static scan stub
- **[medium]** Dep audit stub
- **[medium]** Dependency file: package.json
- **[medium]** Dependency file: pyproject.toml
- **[low]** Tests executed
- **[low]** LLM summary

## Persona Sections
### Code Reviewer
```json
{
  "persona": "Code Reviewer",
  "summary": "Repository & basic APK review completed.",
  "findings": [],
  "artifacts": [],
  "meta": null,
  "metrics": {
    "lint": "ok"
  }
}
```
### Code Reviewer
```json
{
  "persona": "Code Reviewer",
  "summary": "Repository & basic APK review completed.",
  "findings": [],
  "artifacts": [],
  "meta": null,
  "metrics": {
    "lint": "ok"
  }
}
```
### Security Analyst
```json
{
  "persona": "Security Analyst",
  "summary": "Static & binary analysis completed (stubs / real tools where available).",
  "findings": [
    {
      "title": "Static scan stub",
      "description": "Static scan placeholder",
      "severity": "medium",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": null,
      "tags": null
    },
    {
      "title": "Secret-scan heuristic",
      "description": "Heuristic secret scan",
      "severity": "high",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Run git-secrets / truffleHog",
      "evidence": null,
      "tags": null
    },
    {
      "title": "Dep audit stub",
      "description": "Dependency audit placeholder",
      "severity": "medium",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Run safety / npm audit / Snyk",
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null,
  "vulnerabilities": [
    {
      "count": 3
    }
  ]
}
```
### PenTester
```json
{
  "persona": "PenTester",
  "summary": "Dynamic baseline pentest executed (stubs for missing tooling).",
  "findings": [
    {
      "title": "API deep fuzzing",
      "description": "API dynamic stub",
      "severity": "high",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Use auth-aware API fuzzer",
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null,
  "exploits": [],
  "impact_summary": "See findings for impact."
}
```
### Test Engineer
```json
{
  "persona": "Test Engineer",
  "summary": "Test tooling executed (or stubbed) and smoke tests generated.",
  "findings": [
    {
      "title": "Tests executed",
      "description": "pytest placeholder",
      "severity": "low",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [
    "# Auto-generated smoke test\n\ndef test_smoke():\n    assert True\n"
  ],
  "meta": null,
  "coverage": null,
  "failed_tests": []
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "Static Checks",
  "findings": [
    {
      "title": "Dependency file: package.json",
      "description": "",
      "severity": "medium",
      "file": "package.json",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "Static Checks",
  "findings": [
    {
      "title": "Dependency file: pyproject.toml",
      "description": "",
      "severity": "medium",
      "file": "pyproject.toml",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "LLM Code Review",
  "findings": [
    {
      "title": "LLM summary",
      "description": "LLM not available.",
      "severity": "low",
      "file": "",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### Code Reviewer
```json
{
  "persona": "Code Reviewer",
  "summary": "Repository & basic APK review completed.",
  "findings": [],
  "artifacts": [],
  "meta": null,
  "metrics": {
    "lint": "ok"
  }
}
```
### Code Reviewer
```json
{
  "persona": "Code Reviewer",
  "summary": "Repository & basic APK review completed.",
  "findings": [],
  "artifacts": [],
  "meta": null,
  "metrics": {
    "lint": "ok"
  }
}
```
### Security Analyst
```json
{
  "persona": "Security Analyst",
  "summary": "Static & binary analysis completed (stubs / real tools where available).",
  "findings": [
    {
      "title": "Static scan stub",
      "description": "Static scan placeholder",
      "severity": "medium",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": null,
      "tags": null
    },
    {
      "title": "Secret-scan heuristic",
      "description": "Heuristic secret scan",
      "severity": "high",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Run git-secrets / truffleHog",
      "evidence": null,
      "tags": null
    },
    {
      "title": "Dep audit stub",
      "description": "Dependency audit placeholder",
      "severity": "medium",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Run safety / npm audit / Snyk",
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null,
  "vulnerabilities": [
    {
      "count": 3
    }
  ]
}
```
### PenTester
```json
{
  "persona": "PenTester",
  "summary": "Dynamic baseline pentest executed (stubs for missing tooling).",
  "findings": [
    {
      "title": "API deep fuzzing",
      "description": "API dynamic stub",
      "severity": "high",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Use auth-aware API fuzzer",
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null,
  "exploits": [],
  "impact_summary": "See findings for impact."
}
```
### Test Engineer
```json
{
  "persona": "Test Engineer",
  "summary": "Test tooling executed (or stubbed) and smoke tests generated.",
  "findings": [
    {
      "title": "Tests executed",
      "description": "pytest placeholder",
      "severity": "low",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [
    "# Auto-generated smoke test\n\ndef test_smoke():\n    assert True\n"
  ],
  "meta": null,
  "coverage": null,
  "failed_tests": []
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "Static Checks",
  "findings": [
    {
      "title": "Dependency file: package.json",
      "description": "",
      "severity": "medium",
      "file": "package.json",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "Static Checks",
  "findings": [
    {
      "title": "Dependency file: pyproject.toml",
      "description": "",
      "severity": "medium",
      "file": "pyproject.toml",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "LLM Code Review",
  "findings": [
    {
      "title": "LLM summary",
      "description": "LLM not available.",
      "severity": "low",
      "file": "",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### Code Reviewer
```json
{
  "persona": "Code Reviewer",
  "summary": "Repository & basic APK review completed.",
  "findings": [],
  "artifacts": [],
  "meta": null,
  "metrics": {
    "lint": "ok"
  }
}
```
### Code Reviewer
```json
{
  "persona": "Code Reviewer",
  "summary": "Repository & basic APK review completed.",
  "findings": [],
  "artifacts": [],
  "meta": null,
  "metrics": {
    "lint": "ok"
  }
}
```
### Security Analyst
```json
{
  "persona": "Security Analyst",
  "summary": "Static & binary analysis completed (stubs / real tools where available).",
  "findings": [
    {
      "title": "Static scan stub",
      "description": "Static scan placeholder",
      "severity": "medium",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": null,
      "tags": null
    },
    {
      "title": "Secret-scan heuristic",
      "description": "Heuristic secret scan",
      "severity": "high",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Run git-secrets / truffleHog",
      "evidence": null,
      "tags": null
    },
    {
      "title": "Dep audit stub",
      "description": "Dependency audit placeholder",
      "severity": "medium",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Run safety / npm audit / Snyk",
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null,
  "vulnerabilities": [
    {
      "count": 3
    }
  ]
}
```
### PenTester
```json
{
  "persona": "PenTester",
  "summary": "Dynamic baseline pentest executed (stubs for missing tooling).",
  "findings": [
    {
      "title": "API deep fuzzing",
      "description": "API dynamic stub",
      "severity": "high",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Use auth-aware API fuzzer",
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null,
  "exploits": [],
  "impact_summary": "See findings for impact."
}
```
### Test Engineer
```json
{
  "persona": "Test Engineer",
  "summary": "Test tooling executed (or stubbed) and smoke tests generated.",
  "findings": [
    {
      "title": "Tests executed",
      "description": "pytest placeholder",
      "severity": "low",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [
    "# Auto-generated smoke test\n\ndef test_smoke():\n    assert True\n"
  ],
  "meta": null,
  "coverage": null,
  "failed_tests": []
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "Static Checks",
  "findings": [
    {
      "title": "Dependency file: package.json",
      "description": "",
      "severity": "medium",
      "file": "package.json",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "Static Checks",
  "findings": [
    {
      "title": "Dependency file: pyproject.toml",
      "description": "",
      "severity": "medium",
      "file": "pyproject.toml",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "LLM Code Review",
  "findings": [
    {
      "title": "LLM summary",
      "description": "LLM not available.",
      "severity": "low",
      "file": "",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### Code Reviewer
```json
{
  "persona": "Code Reviewer",
  "summary": "Repository & basic APK review completed.",
  "findings": [],
  "artifacts": [],
  "meta": null,
  "metrics": {
    "lint": "ok"
  }
}
```
### Code Reviewer
```json
{
  "persona": "Code Reviewer",
  "summary": "Repository & basic APK review completed.",
  "findings": [],
  "artifacts": [],
  "meta": null,
  "metrics": {
    "lint": "ok"
  }
}
```
### Security Analyst
```json
{
  "persona": "Security Analyst",
  "summary": "Static & binary analysis completed (stubs / real tools where available).",
  "findings": [
    {
      "title": "Static scan stub",
      "description": "Static scan placeholder",
      "severity": "medium",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": null,
      "tags": null
    },
    {
      "title": "Secret-scan heuristic",
      "description": "Heuristic secret scan",
      "severity": "high",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Run git-secrets / truffleHog",
      "evidence": null,
      "tags": null
    },
    {
      "title": "Dep audit stub",
      "description": "Dependency audit placeholder",
      "severity": "medium",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Run safety / npm audit / Snyk",
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null,
  "vulnerabilities": [
    {
      "count": 3
    }
  ]
}
```
### PenTester
```json
{
  "persona": "PenTester",
  "summary": "Dynamic baseline pentest executed (stubs for missing tooling).",
  "findings": [
    {
      "title": "API deep fuzzing",
      "description": "API dynamic stub",
      "severity": "high",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Use auth-aware API fuzzer",
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null,
  "exploits": [],
  "impact_summary": "See findings for impact."
}
```
### Test Engineer
```json
{
  "persona": "Test Engineer",
  "summary": "Test tooling executed (or stubbed) and smoke tests generated.",
  "findings": [
    {
      "title": "Tests executed",
      "description": "pytest placeholder",
      "severity": "low",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [
    "# Auto-generated smoke test\n\ndef test_smoke():\n    assert True\n"
  ],
  "meta": null,
  "coverage": null,
  "failed_tests": []
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "Static Checks",
  "findings": [
    {
      "title": "Dependency file: package.json",
      "description": "",
      "severity": "medium",
      "file": "package.json",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "Static Checks",
  "findings": [
    {
      "title": "Dependency file: pyproject.toml",
      "description": "",
      "severity": "medium",
      "file": "pyproject.toml",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "LLM Code Review",
  "findings": [
    {
      "title": "LLM summary",
      "description": "LLM not available.",
      "severity": "low",
      "file": "",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### Code Reviewer
```json
{
  "persona": "Code Reviewer",
  "summary": "Repository & basic APK review completed.",
  "findings": [],
  "artifacts": [],
  "meta": null,
  "metrics": {
    "lint": "ok"
  }
}
```
### Code Reviewer
```json
{
  "persona": "Code Reviewer",
  "summary": "Repository & basic APK review completed.",
  "findings": [],
  "artifacts": [],
  "meta": null,
  "metrics": {
    "lint": "ok"
  }
}
```
### Security Analyst
```json
{
  "persona": "Security Analyst",
  "summary": "Static & binary analysis completed (stubs / real tools where available).",
  "findings": [
    {
      "title": "Static scan stub",
      "description": "Static scan placeholder",
      "severity": "medium",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": null,
      "tags": null
    },
    {
      "title": "Secret-scan heuristic",
      "description": "Heuristic secret scan",
      "severity": "high",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Run git-secrets / truffleHog",
      "evidence": null,
      "tags": null
    },
    {
      "title": "Dep audit stub",
      "description": "Dependency audit placeholder",
      "severity": "medium",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Run safety / npm audit / Snyk",
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null,
  "vulnerabilities": [
    {
      "count": 3
    }
  ]
}
```
### PenTester
```json
{
  "persona": "PenTester",
  "summary": "Dynamic baseline pentest executed (stubs for missing tooling).",
  "findings": [
    {
      "title": "API deep fuzzing",
      "description": "API dynamic stub",
      "severity": "high",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": "Use auth-aware API fuzzer",
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null,
  "exploits": [],
  "impact_summary": "See findings for impact."
}
```
### Test Engineer
```json
{
  "persona": "Test Engineer",
  "summary": "Test tooling executed (or stubbed) and smoke tests generated.",
  "findings": [
    {
      "title": "Tests executed",
      "description": "pytest placeholder",
      "severity": "low",
      "file": null,
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": null,
      "tags": null
    }
  ],
  "artifacts": [
    "# Auto-generated smoke test\n\ndef test_smoke():\n    assert True\n"
  ],
  "meta": null,
  "coverage": null,
  "failed_tests": []
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "Static Checks",
  "findings": [
    {
      "title": "Dependency file: package.json",
      "description": "",
      "severity": "medium",
      "file": "package.json",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "Static Checks",
  "findings": [
    {
      "title": "Dependency file: pyproject.toml",
      "description": "",
      "severity": "medium",
      "file": "pyproject.toml",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```
### External Agent
```json
{
  "persona": "External Agent",
  "summary": "LLM Code Review",
  "findings": [
    {
      "title": "LLM summary",
      "description": "LLM not available.",
      "severity": "low",
      "file": "",
      "line": null,
      "cwe": null,
      "cvss": null,
      "recommendation": null,
      "evidence": "",
      "tags": null
    }
  ],
  "artifacts": [],
  "meta": null
}
```