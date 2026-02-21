"""
Security Scanner - Detect vulnerabilities and bad patterns.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass, field


@dataclass
class SecurityIssue:
    """A detected security issue."""
    file: str
    line: int
    issue_type: str
    severity: str  # "critical", "high", "medium", "low"
    description: str
    suggestion: str
    cwe: str = ""  # CWE identifier


@dataclass
class SecurityReport:
    """Security scan results."""
    issues: List[SecurityIssue] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    score: int = 100

    def add_issue(self, issue: SecurityIssue):
        self.issues.append(issue)
        if issue.severity == "critical":
            self.critical_count += 1
            self.score = max(0, self.score - 25)
        elif issue.severity == "high":
            self.high_count += 1
            self.score = max(0, self.score - 15)
        elif issue.severity == "medium":
            self.medium_count += 1
            self.score = max(0, self.score - 10)
        else:
            self.low_count += 1
            self.score = max(0, self.score - 5)


# Dangerous patterns
DANGEROUS_PATTERNS = [
    {
        "pattern": r"eval\s*\(",
        "type": "code_injection",
        "severity": "critical",
        "description": "Use of eval() - allows arbitrary code execution",
        "suggestion": "Use ast.literal_eval() for safe evaluation",
        "cwe": "CWE-95"
    },
    {
        "pattern": r"exec\s*\(",
        "type": "code_injection",
        "severity": "critical",
        "description": "Use of exec() - allows arbitrary code execution",
        "suggestion": "Avoid exec(), use safer alternatives",
        "cwe": "CWE-95"
    },
    {
        "pattern": r"subprocess\..*shell\s*=\s*True",
        "type": "command_injection",
        "severity": "high",
        "description": "Shell=True in subprocess - risk of command injection",
        "suggestion": "Use shell=False and pass args as list",
        "cwe": "CWE-78"
    },
    {
        "pattern": r"os\.system\s*\(",
        "type": "command_injection",
        "severity": "high",
        "description": "os.system() - risk of command injection",
        "suggestion": "Use subprocess with shell=False",
        "cwe": "CWE-78"
    },
    {
        "pattern": r"pickle\.loads?\s*\(",
        "type": "deserialization",
        "severity": "high",
        "description": "Pickle deserialization - risk of arbitrary code execution",
        "suggestion": "Use JSON or other safe serialization",
        "cwe": "CWE-502"
    },
    {
        "pattern": r"yaml\.load\s*\([^)]*\)",
        "type": "deserialization",
        "severity": "medium",
        "description": "Unsafe YAML load - use safe_load()",
        "suggestion": "Use yaml.safe_load() instead",
        "cwe": "CWE-502"
    },
    {
        "pattern": r"password\s*=\s*['\"][^'\"]+['\"]",
        "type": "hardcoded_secret",
        "severity": "high",
        "description": "Hardcoded password detected",
        "suggestion": "Use environment variables or secrets manager",
        "cwe": "CWE-798"
    },
    {
        "pattern": r"api_key\s*=\s*['\"][^'\"]+['\"]",
        "type": "hardcoded_secret",
        "severity": "high",
        "description": "Hardcoded API key detected",
        "suggestion": "Use environment variables",
        "cwe": "CWE-798"
    },
    {
        "pattern": r"\.format\s*\([^)]*\)\s*$.*SELECT|INSERT|UPDATE|DELETE",
        "type": "sql_injection",
        "severity": "critical",
        "description": "Potential SQL injection - string formatting in query",
        "suggestion": "Use parameterized queries",
        "cwe": "CWE-89"
    },
    {
        "pattern": r"verify\s*=\s*False",
        "type": "insecure_ssl",
        "severity": "medium",
        "description": "SSL verification disabled",
        "suggestion": "Enable SSL verification",
        "cwe": "CWE-295"
    },
]


class SecurityScanner:
    """
    Scan for security vulnerabilities.

    Detects:
    - Code injection (eval, exec)
    - Command injection (os.system, shell=True)
    - Hardcoded secrets
    - Insecure deserialization
    - SQL injection patterns
    """

    def __init__(self):
        self.report = SecurityReport()

    def scan(self, project_path: Path) -> SecurityReport:
        """Scan project for security issues."""
        self.report = SecurityReport()

        for py_file in project_path.rglob("*.py"):
            if self._should_skip(py_file):
                continue
            self._scan_file(py_file)

        return self.report

    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        skip_patterns = ["__pycache__", ".git", ".venv", "venv", "node_modules", "test"]
        return any(p in path.parts for p in skip_patterns)

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single file."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except:
            return

        lines = content.split("\n")

        for pattern_info in DANGEROUS_PATTERNS:
            pattern = pattern_info["pattern"]
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    self.report.add_issue(SecurityIssue(
                        file=str(file_path),
                        line=i,
                        issue_type=pattern_info["type"],
                        severity=pattern_info["severity"],
                        description=pattern_info["description"],
                        suggestion=pattern_info["suggestion"],
                        cwe=pattern_info.get("cwe", "")
                    ))
