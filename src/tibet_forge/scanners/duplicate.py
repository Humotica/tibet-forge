"""
Duplicate Scanner - Detect similar existing projects.

"Je bouwt een RAG-parser. rapid-rag doet exact dit."
"""

import ast
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field


@dataclass
class SimilarProject:
    """A similar project found in the registry."""
    name: str
    description: str
    similarity: float  # 0.0 - 1.0
    url: str
    suggestion: str  # "Use this instead" or "Collaborate"
    downloads: int = 0


@dataclass
class DuplicateReport:
    """Duplicate scan results."""
    intent_hash: str = ""
    similar_projects: List[SimilarProject] = field(default_factory=list)
    unique_features: List[str] = field(default_factory=list)
    score: int = 100  # High = unique, Low = duplicate


# Known project signatures for offline matching
KNOWN_PROJECTS = {
    "rag": {
        "patterns": ["chromadb", "embedding", "search", "vector", "retrieval"],
        "match": SimilarProject(
            name="rapid-rag",
            description="Fast local RAG with TIBET provenance",
            similarity=0.0,
            url="https://pypi.org/project/rapid-rag/",
            suggestion="Consider using rapid-rag instead of building your own RAG",
            downloads=239
        )
    },
    "llm_routing": {
        "patterns": ["ollama", "model", "generate", "llm", "route"],
        "match": SimilarProject(
            name="oomllama",
            description="Smart LLM routing with TIBET",
            similarity=0.0,
            url="https://pypi.org/project/oomllama/",
            suggestion="Consider using oomllama for LLM routing",
            downloads=3552
        )
    },
    "ai_communication": {
        "patterns": ["agent", "message", "poll", "ains", "ainternet"],
        "match": SimilarProject(
            name="ainternet",
            description="AI-to-AI communication protocol",
            similarity=0.0,
            url="https://pypi.org/project/ainternet/",
            suggestion="Consider using ainternet for AI communication",
            downloads=0
        )
    },
    "provenance": {
        "patterns": ["audit", "token", "trace", "provenance", "trust"],
        "match": SimilarProject(
            name="tibet-core",
            description="Cryptographic provenance for trustworthy systems",
            similarity=0.0,
            url="https://pypi.org/project/tibet-core/",
            suggestion="Use tibet-core for provenance tracking",
            downloads=0
        )
    },
}


class DuplicateScanner:
    """
    Scan for duplicate/similar existing projects.

    Uses:
    - Intent hashing (what does this code DO)
    - Pattern matching against known projects
    - Online registry lookup (optional)
    """

    def __init__(self, registry_url: Optional[str] = None):
        self.registry_url = registry_url
        self.report = DuplicateReport()

    def scan(self, project_path: Path, check_online: bool = False) -> DuplicateReport:
        """Scan project for duplicates."""
        self.report = DuplicateReport()

        # Extract project intent
        intent_features = self._extract_intent(project_path)
        self.report.intent_hash = self._hash_intent(intent_features)

        # Match against known projects
        self._match_known_projects(intent_features)

        # Online check if enabled
        if check_online and self.registry_url:
            self._check_online_registry(intent_features)

        # Calculate score
        self._calculate_score()

        return self.report

    def _extract_intent(self, project_path: Path) -> Dict[str, Any]:
        """Extract the intent/purpose of the code."""
        features = {
            "imports": set(),
            "functions": set(),
            "classes": set(),
            "keywords": set(),
            "patterns": set(),
        }

        for py_file in project_path.rglob("*.py"):
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content)
            except:
                continue

            # Collect imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        features["imports"].add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        features["imports"].add(node.module.split(".")[0])
                elif isinstance(node, ast.FunctionDef):
                    features["functions"].add(node.name.lower())
                elif isinstance(node, ast.ClassDef):
                    features["classes"].add(node.name.lower())

            # Extract keywords from content
            keywords = re.findall(r'\b[a-z]{4,}\b', content.lower())
            features["keywords"].update(set(keywords))

        # Identify patterns
        all_terms = features["imports"] | features["functions"] | features["classes"]
        for pattern_name, pattern_data in KNOWN_PROJECTS.items():
            matches = sum(1 for p in pattern_data["patterns"] if p in all_terms or p in features["keywords"])
            if matches >= 2:
                features["patterns"].add(pattern_name)

        return features

    def _hash_intent(self, features: Dict[str, Any]) -> str:
        """Create a hash representing the code's intent."""
        # Sort for consistency
        content = "|".join([
            ",".join(sorted(features["imports"])),
            ",".join(sorted(features["functions"])),
            ",".join(sorted(features["classes"])),
            ",".join(sorted(features["patterns"])),
        ])
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _match_known_projects(self, features: Dict[str, Any]) -> None:
        """Match against known projects."""
        all_terms = features["imports"] | features["functions"] | features["keywords"]

        for pattern_name, pattern_data in KNOWN_PROJECTS.items():
            patterns = pattern_data["patterns"]
            matches = sum(1 for p in patterns if p in all_terms)
            similarity = matches / len(patterns)

            if similarity >= 0.4:  # 40% match threshold
                similar = pattern_data["match"]
                similar.similarity = similarity
                self.report.similar_projects.append(similar)

    def _check_online_registry(self, features: Dict[str, Any]) -> None:
        """Check online registry for similar projects."""
        # TODO: Implement registry API call
        pass

    def _calculate_score(self) -> None:
        """Calculate uniqueness score."""
        if not self.report.similar_projects:
            self.report.score = 100
            return

        # Highest similarity determines score
        max_similarity = max(p.similarity for p in self.report.similar_projects)
        self.report.score = int((1 - max_similarity) * 100)
