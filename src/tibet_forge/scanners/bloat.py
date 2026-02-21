"""
Bloat Scanner - Detect unnecessary dependencies and code.

"Je importeert requests maar gebruikt alleen een GET"
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any
from dataclasses import dataclass, field


# Heavy dependencies that often have lighter alternatives
HEAVY_DEPS = {
    "requests": {
        "size": "large",
        "alternative": "httpx or urllib3",
        "reason": "requests pulls in many transitive deps"
    },
    "beautifulsoup4": {
        "size": "large",
        "alternative": "selectolax or lxml",
        "reason": "bs4 is slow, lighter alternatives exist"
    },
    "pandas": {
        "size": "huge",
        "alternative": "polars or duckdb",
        "reason": "pandas is 50MB+, consider if you need it all"
    },
    "tensorflow": {
        "size": "huge",
        "alternative": "pytorch or onnxruntime",
        "reason": "TF is massive, do you need the full framework?"
    },
    "django": {
        "size": "huge",
        "alternative": "fastapi or flask",
        "reason": "Django is batteries-included, maybe too many batteries?"
    },
}

# Common unused imports patterns
COMMONLY_UNUSED = [
    "typing",  # Often over-imported
    "os",      # Imported but Path used instead
    "sys",     # Imported "just in case"
    "json",    # Sometimes imported but not used
]


@dataclass
class BloatIssue:
    """A detected bloat issue."""
    file: str
    line: int
    issue_type: str  # "heavy_dep", "unused_import", "dead_code"
    description: str
    suggestion: str
    severity: str = "warning"  # "warning", "error", "info"


@dataclass
class BloatReport:
    """Bloat scan results."""
    issues: List[BloatIssue] = field(default_factory=list)
    total_imports: int = 0
    unused_imports: int = 0
    heavy_deps: List[str] = field(default_factory=list)
    score: int = 100  # Starts perfect, deductions for issues

    def add_issue(self, issue: BloatIssue):
        self.issues.append(issue)
        # Deduct points
        if issue.severity == "error":
            self.score = max(0, self.score - 10)
        elif issue.severity == "warning":
            self.score = max(0, self.score - 5)
        else:
            self.score = max(0, self.score - 2)


class BloatScanner:
    """
    Scan for code bloat.

    Detects:
    - Heavy dependencies with lighter alternatives
    - Unused imports
    - Dead code patterns
    """

    def __init__(self):
        self.report = BloatReport()

    def scan(self, project_path: Path) -> BloatReport:
        """Scan project for bloat."""
        self.report = BloatReport()

        # Scan Python files
        for py_file in project_path.rglob("*.py"):
            if self._should_skip(py_file):
                continue
            self._scan_file(py_file)

        # Check requirements/pyproject for heavy deps
        self._scan_dependencies(project_path)

        return self.report

    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        skip_patterns = ["__pycache__", ".git", ".venv", "venv", "node_modules"]
        return any(p in path.parts for p in skip_patterns)

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single Python file."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
        except SyntaxError:
            return

        # Collect imports and usages
        imports = self._collect_imports(tree)
        usages = self._collect_usages(tree, content)

        self.report.total_imports += len(imports)

        # Check for unused imports
        for imp_name, imp_line in imports.items():
            if imp_name not in usages and imp_name not in ["*"]:
                self.report.unused_imports += 1
                self.report.add_issue(BloatIssue(
                    file=str(file_path),
                    line=imp_line,
                    issue_type="unused_import",
                    description=f"Unused import: {imp_name}",
                    suggestion=f"Remove 'import {imp_name}' or use it",
                    severity="warning"
                ))

        # Check for heavy dependencies used in code
        for imp_name, imp_line in imports.items():
            if imp_name in HEAVY_DEPS:
                info = HEAVY_DEPS[imp_name]
                if imp_name not in self.report.heavy_deps:
                    self.report.heavy_deps.append(imp_name)
                    self.report.add_issue(BloatIssue(
                        file=str(file_path),
                        line=imp_line,
                        issue_type="heavy_dep",
                        description=f"Heavy dependency: {imp_name}",
                        suggestion=f"Consider: {info['alternative']}",
                        severity="info"
                    ))

    def _collect_imports(self, tree: ast.AST) -> Dict[str, int]:
        """Collect all imports with line numbers."""
        imports = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name.split(".")[0]] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        name = alias.asname or alias.name
                        imports[name] = node.lineno

        return imports

    def _collect_usages(self, tree: ast.AST, content: str) -> Set[str]:
        """Collect all name usages."""
        usages = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                usages.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    usages.add(node.value.id)

        return usages

    def _scan_dependencies(self, project_path: Path) -> None:
        """Scan dependency files for heavy deps."""
        dep_files = [
            project_path / "requirements.txt",
            project_path / "pyproject.toml",
            project_path / "setup.py",
        ]

        deps_found = set()

        for dep_file in dep_files:
            if dep_file.exists():
                content = dep_file.read_text(encoding="utf-8", errors="ignore")
                for dep in HEAVY_DEPS:
                    if dep in content.lower():
                        deps_found.add(dep)

        for dep in deps_found:
            info = HEAVY_DEPS[dep]
            self.report.heavy_deps.append(dep)
            self.report.add_issue(BloatIssue(
                file="dependencies",
                line=0,
                issue_type="heavy_dep",
                description=f"Heavy dependency: {dep} ({info['size']})",
                suggestion=f"Consider: {info['alternative']}. {info['reason']}",
                severity="info" if info["size"] == "large" else "warning"
            ))
