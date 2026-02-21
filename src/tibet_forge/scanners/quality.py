"""
Quality Scanner - Code quality and documentation checks.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass, field


@dataclass
class QualityReport:
    """Quality scan results."""
    has_readme: bool = False
    has_license: bool = False
    has_tests: bool = False
    has_docstrings: bool = False
    has_type_hints: bool = False
    has_pyproject: bool = False

    total_functions: int = 0
    documented_functions: int = 0
    typed_functions: int = 0

    total_classes: int = 0
    documented_classes: int = 0

    score: int = 0

    def calculate_score(self):
        """Calculate quality score."""
        score = 0

        # Project structure (40 points)
        if self.has_readme:
            score += 15
        if self.has_license:
            score += 10
        if self.has_tests:
            score += 10
        if self.has_pyproject:
            score += 5

        # Documentation (30 points)
        if self.total_functions > 0:
            doc_ratio = self.documented_functions / self.total_functions
            score += int(doc_ratio * 20)

        if self.total_classes > 0:
            class_doc_ratio = self.documented_classes / self.total_classes
            score += int(class_doc_ratio * 10)

        # Type hints (30 points)
        if self.total_functions > 0:
            type_ratio = self.typed_functions / self.total_functions
            score += int(type_ratio * 30)

        self.score = min(100, score)


class QualityScanner:
    """
    Scan for code quality.

    Checks:
    - README presence
    - License presence
    - Test presence
    - Docstrings
    - Type hints
    """

    def __init__(self):
        self.report = QualityReport()

    def scan(self, project_path: Path) -> QualityReport:
        """Scan project for quality."""
        self.report = QualityReport()

        # Check project files
        self._check_project_files(project_path)

        # Scan Python files
        for py_file in project_path.rglob("*.py"):
            if self._should_skip(py_file):
                continue
            self._scan_file(py_file)

        self.report.calculate_score()
        return self.report

    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        skip_patterns = ["__pycache__", ".git", ".venv", "venv", "node_modules"]
        return any(p in path.parts for p in skip_patterns)

    def _check_project_files(self, project_path: Path) -> None:
        """Check for essential project files."""
        # README
        readme_patterns = ["README.md", "README.rst", "README.txt", "README"]
        self.report.has_readme = any((project_path / p).exists() for p in readme_patterns)

        # License
        license_patterns = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
        self.report.has_license = any((project_path / p).exists() for p in license_patterns)

        # Tests
        test_patterns = ["tests", "test", "tests.py", "test.py"]
        self.report.has_tests = any((project_path / p).exists() for p in test_patterns)

        # pyproject.toml
        self.report.has_pyproject = (project_path / "pyproject.toml").exists()

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single Python file."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
        except:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.report.total_functions += 1

                # Check docstring
                if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    self.report.documented_functions += 1
                    self.report.has_docstrings = True

                # Check type hints
                if node.returns or any(arg.annotation for arg in node.args.args):
                    self.report.typed_functions += 1
                    self.report.has_type_hints = True

            elif isinstance(node, ast.ClassDef):
                self.report.total_classes += 1

                # Check docstring
                if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    self.report.documented_classes += 1
