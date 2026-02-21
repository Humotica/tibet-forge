"""
tibet-forge CLI - From vibe code to trusted tool.
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


console = Console()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="tibet-forge",
        description="From vibe code to trusted tool. The Let's Encrypt of AI provenance."
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan project for issues")
    scan_parser.add_argument("path", nargs="?", default=".", help="Project path")
    scan_parser.add_argument("--no-bloat", action="store_true", help="Skip bloat check")
    scan_parser.add_argument("--no-duplicates", action="store_true", help="Skip duplicate check")
    scan_parser.add_argument("--no-security", action="store_true", help="Skip security check")

    # Certify command
    certify_parser = subparsers.add_parser("certify", help="Full certification pipeline")
    certify_parser.add_argument("path", nargs="?", default=".", help="Project path")
    certify_parser.add_argument("--no-wrap", action="store_true", help="Don't auto-wrap")

    # Score command
    score_parser = subparsers.add_parser("score", help="Show trust score only")
    score_parser.add_argument("path", nargs="?", default=".", help="Project path")

    # Wrap command
    wrap_parser = subparsers.add_parser("wrap", help="Inject TIBET provenance")
    wrap_parser.add_argument("path", nargs="?", default=".", help="Project path")
    wrap_parser.add_argument("--dry-run", action="store_true", help="Show what would be done")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize tibet-forge config")
    init_parser.add_argument("path", nargs="?", default=".", help="Project path")

    args = parser.parse_args()

    if args.command is None:
        _show_banner()
        parser.print_help()
        return 0

    if args.command == "scan":
        return _cmd_scan(args)
    elif args.command == "certify":
        return _cmd_certify(args)
    elif args.command == "score":
        return _cmd_score(args)
    elif args.command == "wrap":
        return _cmd_wrap(args)
    elif args.command == "init":
        return _cmd_init(args)

    return 0


def _show_banner():
    """Show tibet-forge banner."""
    banner = """
╔════════════════════════════════════════════════════════╗
║                    tibet-forge                          ║
║         From vibe code to trusted tool                  ║
║                                                         ║
║  The Let's Encrypt of AI provenance                     ║
╚════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold blue")


def _cmd_scan(args) -> int:
    """Run scan command."""
    from .forge import Forge
    from .config import ForgeConfig

    path = Path(args.path)
    if not path.exists():
        console.print(f"[red]Error: Path not found: {path}[/red]")
        return 1

    config = ForgeConfig()
    config.scan_bloat = not args.no_bloat
    config.scan_duplicates = not args.no_duplicates
    config.scan_security = not args.no_security

    forge = Forge(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("Scanning project...", total=None)
        result = forge.scan(path)

    _display_result(result)
    return 0


def _cmd_certify(args) -> int:
    """Run certify command."""
    from .forge import Forge
    from .config import ForgeConfig

    path = Path(args.path)
    if not path.exists():
        console.print(f"[red]Error: Path not found: {path}[/red]")
        return 1

    config = ForgeConfig()
    config.auto_wrap = not args.no_wrap

    forge = Forge(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("Certifying project...", total=None)
        result = forge.certify(path)

    _display_result(result)

    if result.certified:
        console.print("\n[bold green]✓ CERTIFIED[/bold green]")
        console.print(f"\nBadge markdown:\n{result.badge_markdown}")
    else:
        console.print(f"\n[yellow]Not certified (score {result.trust_score.total} < 70)[/yellow]")

    return 0


def _cmd_score(args) -> int:
    """Show trust score only."""
    from .forge import Forge

    path = Path(args.path)
    forge = Forge()
    result = forge.scan(path)

    score = result.trust_score

    # Big score display
    color = "green" if score.total >= 70 else "yellow" if score.total >= 50 else "red"
    console.print(Panel(
        f"[bold {color}]{score.total}[/bold {color}] / 100\n"
        f"Grade: [bold]{score.grade}[/bold]",
        title="Humotica Trust Score",
        border_style=color
    ))

    return 0


def _cmd_wrap(args) -> int:
    """Run wrap command."""
    from .wrappers import TibetInjector

    path = Path(args.path)
    injector = TibetInjector()

    report = injector.inject(path, dry_run=args.dry_run)

    console.print(f"\nFiles analyzed: {report['files_analyzed']}")
    console.print(f"Injection points: {report['injection_points']}")

    if report["actions"]:
        table = Table(title="Injection Points")
        table.add_column("File")
        table.add_column("Line")
        table.add_column("Category")
        table.add_column("Action")

        for action in report["actions"][:20]:
            table.add_row(
                action["file"].split("/")[-1],
                str(action["line"]),
                action["category"],
                action["action"]
            )

        console.print(table)

    if args.dry_run:
        console.print("\n[yellow]Dry run - no changes made[/yellow]")
    else:
        console.print("\n[green]Injections applied[/green]")

    return 0


def _cmd_init(args) -> int:
    """Initialize config."""
    from .config import ForgeConfig

    path = Path(args.path)
    config_file = path / "tibet-forge.json"

    if config_file.exists():
        console.print(f"[yellow]Config already exists: {config_file}[/yellow]")
        return 1

    config = ForgeConfig.load(path)
    config.save(config_file)

    console.print(f"[green]Created: {config_file}[/green]")
    return 0


def _display_result(result) -> None:
    """Display forge result."""
    console.print("\n" + "=" * 60)
    console.print(result.trust_score.summary())
    console.print("=" * 60)

    # Bloat issues
    if result.bloat_report and result.bloat_report.issues:
        console.print("\n[bold]Bloat Issues:[/bold]")
        for issue in result.bloat_report.issues[:5]:
            console.print(f"  [yellow]•[/yellow] {issue.description}")
            console.print(f"    → {issue.suggestion}")

    # Security issues
    if result.security_report and result.security_report.issues:
        console.print("\n[bold]Security Issues:[/bold]")
        for issue in result.security_report.issues[:5]:
            color = "red" if issue.severity in ["critical", "high"] else "yellow"
            console.print(f"  [{color}]•[/{color}] [{issue.severity.upper()}] {issue.description}")
            console.print(f"    → {issue.suggestion}")

    # Similar projects
    if result.duplicate_report and result.duplicate_report.similar_projects:
        console.print("\n[bold]Similar Projects Found:[/bold]")
        for proj in result.duplicate_report.similar_projects:
            console.print(f"  [blue]•[/blue] {proj.name} ({proj.similarity:.0%} similar)")
            console.print(f"    {proj.suggestion}")
            console.print(f"    {proj.url}")


if __name__ == "__main__":
    sys.exit(main())
