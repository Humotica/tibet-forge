"""
Hall of Shame - The public wall of code disgrace.

"Shitcoder van de maand" - celebrating the worst of the worst.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# Category-specific roasts
SHAME_ROASTS = {
    "bloat_king": [
        "Congratulations! You imported the entire universe for a Hello World.",
        "Your node_modules called - they want their bloat crown back.",
        "This code is so heavy, it needs its own gravitational field.",
    ],
    "security_nightmare": [
        "This code is so insecure, hackers use it as a tutorial.",
        "eval(), exec(), AND hardcoded passwords? You're speedrunning CVEs.",
        "The CISO just had a heart attack looking at this. Thanks.",
    ],
    "spaghetti_master": [
        "This code has more nesting than a Russian doll factory.",
        "I've seen cleaner code written by a cat walking on a keyboard.",
        "The arrow anti-pattern called - you've achieved final form.",
    ],
    "deprecated_dinosaur": [
        "This code belongs in a museum, not production.",
        "Using Python 2 syntax in 2025? Bold strategy.",
        "Your dependencies are so old, they remember dial-up.",
    ],
    "latency_legend": [
        "This code is slower than a sloth on sedatives.",
        "O(n!) complexity? Did you WANT to boil the ocean?",
        "Your API calls have API calls. It's turtles all the way down.",
    ],
    "llm_hallucinator": [
        "You copy-pasted from ChatGPT and didn't even read it, did you?",
        "The AI wrote this and you just... shipped it? Brave.",
        "'Sure, here is the code' - still in your docstring. Chef's kiss.",
    ],
    "over_engineer": [
        "You built a spaceship to go to the grocery store.",
        "AbstractFactoryBuilderStrategyPatternImpl for a TODO app? Really?",
        "This has more design patterns than actual functionality.",
    ],
}


@dataclass
class ShameEntry:
    """A Hall of Shame entry."""
    repo_url: str
    repo_name: str
    score: int
    grade: str
    category: str
    roast: str
    highlights: List[str] = field(default_factory=list)
    submitted_at: str = ""
    shame_id: str = ""

    def __post_init__(self):
        if not self.submitted_at:
            self.submitted_at = datetime.now().isoformat()
        if not self.shame_id:
            self.shame_id = hashlib.sha256(
                f"{self.repo_url}{self.submitted_at}".encode()
            ).hexdigest()[:12]


@dataclass
class HallOfShame:
    """The glorious Hall of Shame."""
    entries: List[ShameEntry] = field(default_factory=list)
    last_updated: str = ""

    # Awards
    shitcoder_of_month: Optional[ShameEntry] = None
    bloat_king: Optional[ShameEntry] = None
    security_nightmare: Optional[ShameEntry] = None
    spaghetti_master: Optional[ShameEntry] = None

    def add_entry(self, entry: ShameEntry):
        """Add a new shame entry."""
        self.entries.append(entry)
        self.entries.sort(key=lambda e: e.score)  # Lowest first = most shame
        self.last_updated = datetime.now().isoformat()
        self._update_awards()

    def _update_awards(self):
        """Update the shame awards."""
        if not self.entries:
            return

        # Shitcoder of the month = lowest score
        self.shitcoder_of_month = self.entries[0]

        # Category winners
        for entry in self.entries:
            if entry.category == "bloat_king" and (
                not self.bloat_king or entry.score < self.bloat_king.score
            ):
                self.bloat_king = entry
            elif entry.category == "security_nightmare" and (
                not self.security_nightmare or entry.score < self.security_nightmare.score
            ):
                self.security_nightmare = entry
            elif entry.category == "spaghetti_master" and (
                not self.spaghetti_master or entry.score < self.spaghetti_master.score
            ):
                self.spaghetti_master = entry

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "entries": [asdict(e) for e in self.entries],
            "last_updated": self.last_updated,
            "awards": {
                "shitcoder_of_month": asdict(self.shitcoder_of_month) if self.shitcoder_of_month else None,
                "bloat_king": asdict(self.bloat_king) if self.bloat_king else None,
                "security_nightmare": asdict(self.security_nightmare) if self.security_nightmare else None,
                "spaghetti_master": asdict(self.spaghetti_master) if self.spaghetti_master else None,
            }
        }

    def save(self, path: Path):
        """Save to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "HallOfShame":
        """Load from JSON file."""
        if not path.exists():
            return cls()
        with open(path) as f:
            data = json.load(f)

        hall = cls()
        for entry_data in data.get("entries", []):
            hall.entries.append(ShameEntry(**entry_data))
        hall.last_updated = data.get("last_updated", "")
        hall._update_awards()
        return hall


def determine_shame_category(result) -> str:
    """Determine the primary shame category based on scan results."""
    scores = {
        "bloat_king": 100,
        "security_nightmare": 100,
        "spaghetti_master": 100,
        "over_engineer": 100,
    }

    # Check bloat
    if result.bloat_report:
        if result.bloat_report.unused_imports > 10:
            scores["bloat_king"] -= 30
        if result.bloat_report.heavy_deps:
            scores["bloat_king"] -= 20 * len(result.bloat_report.heavy_deps)

    # Check security
    if result.security_report:
        scores["security_nightmare"] -= result.security_report.critical_count * 25
        scores["security_nightmare"] -= result.security_report.high_count * 15

    # Check quality (spaghetti)
    if result.quality_report:
        arrow_smells = sum(1 for s in result.quality_report.smells if s.smell_type == "arrow_pattern")
        scores["spaghetti_master"] -= arrow_smells * 20

        long_names = sum(1 for s in result.quality_report.smells if s.smell_type == "long_name")
        scores["over_engineer"] -= long_names * 15

    # Return lowest (worst) category
    return min(scores, key=scores.get)


def generate_custom_roast(result, category: str) -> str:
    """Generate a custom roast based on scan results."""
    import random

    base_roast = random.choice(SHAME_ROASTS.get(category, SHAME_ROASTS["over_engineer"]))

    # Add specific details
    extras = []

    if result.bloat_report and result.bloat_report.unused_imports > 5:
        extras.append(f"{result.bloat_report.unused_imports} unused imports")

    if result.security_report and result.security_report.critical_count > 0:
        extras.append(f"{result.security_report.critical_count} critical vulnerabilities")

    if result.quality_report:
        llm_artifacts = sum(1 for s in result.quality_report.smells if s.smell_type == "llm_artifact")
        if llm_artifacts > 0:
            extras.append("AI-generated code leftovers")

    if extras:
        return f"{base_roast} Bonus points for: {', '.join(extras)}."

    return base_roast


def generate_highlights(result) -> List[str]:
    """Generate shame highlights from scan results."""
    highlights = []

    # Security horrors
    if result.security_report:
        for issue in result.security_report.issues[:3]:
            highlights.append(f"[{issue.severity.upper()}] {issue.description}")

    # Bloat champions
    if result.bloat_report:
        for issue in result.bloat_report.issues[:2]:
            highlights.append(issue.description)

    # Quality smells
    if result.quality_report:
        for smell in result.quality_report.smells[:2]:
            highlights.append(f"{smell.smell_type}: {smell.context[:30]}...")

    return highlights[:5]  # Max 5 highlights


def format_shame_display(hall: HallOfShame) -> str:
    """Format the Hall of Shame for terminal display."""
    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║            🏆 HALL OF SHAME 🏆                               ║",
        "║         Where bad code comes to be celebrated                 ║",
        "╚══════════════════════════════════════════════════════════════╝",
        "",
    ]

    # Awards section
    if hall.shitcoder_of_month:
        lines.append("👑 SHITCODER OF THE MONTH:")
        e = hall.shitcoder_of_month
        lines.append(f"   {e.repo_name} - Score: {e.score}/100 ({e.grade})")
        lines.append(f"   {e.repo_url}")
        lines.append(f"   \"{e.roast}\"")
        lines.append("")

    # Category winners
    categories = [
        ("bloat_king", "💀 BLOAT KING", hall.bloat_king),
        ("security_nightmare", "🔓 SECURITY NIGHTMARE", hall.security_nightmare),
        ("spaghetti_master", "🍝 SPAGHETTI MASTER", hall.spaghetti_master),
    ]

    for cat_id, title, entry in categories:
        if entry and entry != hall.shitcoder_of_month:
            lines.append(f"{title}:")
            lines.append(f"   {entry.repo_name} - {entry.score}/100")
            lines.append("")

    # Recent entries
    lines.append("━" * 60)
    lines.append("RECENT SUBMISSIONS:")
    lines.append("")

    for entry in hall.entries[:10]:
        lines.append(f"  [{entry.grade}] {entry.repo_name}")
        lines.append(f"      Score: {entry.score}/100 | Category: {entry.category}")
        lines.append(f"      {entry.roast[:60]}...")
        lines.append("")

    if not hall.entries:
        lines.append("  No entries yet. Submit your shame with:")
        lines.append("  tibet-forge shame --submit <github-url>")
        lines.append("")

    return "\n".join(lines)
