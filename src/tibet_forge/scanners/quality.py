"""
Quality Scanner - Code quality and documentation checks.

The Gordon Ramsay of code review.
"""

import ast
from pathlib import Path
from typing import List
from dataclasses import dataclass, field


# Gordon Ramsay-style roasts for code smells
ROASTS = {
    "long_name": "If you keep using sentences like this to code, you'd better start coding tea parties.",
    "arrow_pattern": "Are we building software or a staircase to hell? Flatten this out.",
    "except_pass": "Catching all exceptions and doing nothing? Just close your eyes while driving on the highway, it's the same thing.",
    "god_file": "This file is longer than a CVS receipt. Break it up before it gains sentience.",
    "llm_artifact": "You left the AI's polite small talk in your codebase. Clean up your room.",
}


@dataclass
class CodeSmell:
    """A detected code smell with a roast."""
    file: str
    line: int
    smell_type: str
    roast: str
    context: str = ""


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

    smells: List[CodeSmell] = field(default_factory=list)
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

        lines = content.split("\n")
        filename = str(file_path)

        # Check for God File (>1000 lines)
        if len(lines) > 1000:
            self.report.smells.append(CodeSmell(
                file=filename, line=1, smell_type="god_file",
                roast=ROASTS["god_file"],
                context=f"{len(lines)} lines"
            ))

        # Check for LLM artifacts
        llm_patterns = ["Sure, here is", "Here's the code", "I'll help you",
                       "Let me explain", "As an AI", "I cannot"]
        for i, line in enumerate(lines, 1):
            for pattern in llm_patterns:
                if pattern in line and ('"""' in line or "'''" in line or "#" in line):
                    self.report.smells.append(CodeSmell(
                        file=filename, line=i, smell_type="llm_artifact",
                        roast=ROASTS["llm_artifact"],
                        context=line.strip()[:50]
                    ))
                    break

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.report.total_functions += 1

                # Check for long names (>35 chars)
                if len(node.name) > 35:
                    self.report.smells.append(CodeSmell(
                        file=filename, line=node.lineno, smell_type="long_name",
                        roast=ROASTS["long_name"],
                        context=node.name
                    ))

                # Check for arrow anti-pattern (nested depth > 3)
                depth = self._max_nesting_depth(node)
                if depth > 3:
                    self.report.smells.append(CodeSmell(
                        file=filename, line=node.lineno, smell_type="arrow_pattern",
                        roast=ROASTS["arrow_pattern"],
                        context=f"Nesting depth: {depth}"
                    ))

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

                # Check for long class names
                if len(node.name) > 35:
                    self.report.smells.append(CodeSmell(
                        file=filename, line=node.lineno, smell_type="long_name",
                        roast=ROASTS["long_name"],
                        context=node.name
                    ))

                # Check docstring
                if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    self.report.documented_classes += 1

            # Check for except pass
            elif isinstance(node, ast.ExceptHandler):
                if node.body and len(node.body) == 1:
                    if isinstance(node.body[0], ast.Pass):
                        self.report.smells.append(CodeSmell(
                            file=filename, line=node.lineno, smell_type="except_pass",
                            roast=ROASTS["except_pass"],
                            context="except: pass"
                        ))

    def _max_nesting_depth(self, node: ast.AST, current: int = 0) -> int:
        """Calculate maximum nesting depth of for/if/while loops."""
        max_depth = current
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While, ast.If, ast.With)):
                child_depth = self._max_nesting_depth(child, current + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._max_nesting_depth(child, current)
                max_depth = max(max_depth, child_depth)
        return max_depth
