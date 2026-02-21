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

    # Shame command
    shame_parser = subparsers.add_parser("shame", help="Hall of Shame - celebrate bad code")
    shame_parser.add_argument("--submit", type=str, help="Submit a GitHub repo to the Hall of Shame")
    shame_parser.add_argument("--show", action="store_true", help="Show the Hall of Shame")
    shame_parser.add_argument("--local", type=str, help="Shame a local project")

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
    elif args.command == "shame":
        return _cmd_shame(args)

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


def _cmd_shame(args) -> int:
    """Hall of Shame command."""
    from .shame import (
        HallOfShame, ShameEntry, format_shame_display,
        determine_shame_category, generate_custom_roast, generate_highlights
    )
    from .forge import Forge

    shame_file = Path.home() / ".tibet-forge" / "hall_of_shame.json"
    shame_file.parent.mkdir(parents=True, exist_ok=True)

    hall = HallOfShame.load(shame_file)

    if args.show or (not args.submit and not args.local):
        # Show the Hall of Shame
        console.print(format_shame_display(hall))
        return 0

    # Shame a project
    if args.local:
        project_path = Path(args.local)
        repo_url = f"local://{project_path.absolute()}"
        repo_name = project_path.name
    elif args.submit:
        repo_url = args.submit
        # Extract repo name from URL
        repo_name = args.submit.split("/")[-1].replace(".git", "")
        # TODO: Clone and scan GitHub repo
        console.print(f"[yellow]GitHub scanning coming soon![/yellow]")
        console.print(f"For now, clone the repo and use: tibet-forge shame --local ./path")
        return 0

    # Scan the project
    forge = Forge()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(f"Shaming {repo_name}...", total=None)
        result = forge.scan(project_path)

    # Determine shame category and generate roast
    category = determine_shame_category(result)
    roast = generate_custom_roast(result, category)
    highlights = generate_highlights(result)

    # Create shame entry
    entry = ShameEntry(
        repo_url=repo_url,
        repo_name=repo_name,
        score=result.trust_score.total,
        grade=result.trust_score.grade,
        category=category,
        roast=roast,
        highlights=highlights
    )

    hall.add_entry(entry)
    hall.save(shame_file)

    # Display the shame
    console.print("\n" + "=" * 60)
    console.print("[bold red]🔥 SHAME ENTRY CREATED 🔥[/bold red]")
    console.print("=" * 60)
    console.print(f"\n[bold]{repo_name}[/bold]")
    console.print(f"Score: [red]{entry.score}/100[/red] ({entry.grade})")
    console.print(f"Category: [magenta]{entry.category}[/magenta]")
    console.print(f"\n[italic]\"{entry.roast}\"[/italic]")

    if highlights:
        console.print("\n[bold]Lowlights:[/bold]")
        for h in highlights:
            console.print(f"  💀 {h}")

    # Check for awards
    if hall.shitcoder_of_month and hall.shitcoder_of_month.shame_id == entry.shame_id:
        console.print("\n[bold yellow]🏆 CONGRATULATIONS! You are the SHITCODER OF THE MONTH! 🏆[/bold yellow]")

    console.print(f"\n[dim]View all shame: tibet-forge shame --show[/dim]")

    return 0


def _display_result(result) -> None:
    """Display forge result."""
    score = result.trust_score

    # Grade message with attitude
    grade_msg = score.grade_message()
    if score.total >= 90:
        console.print(f"\n[bold green]{grade_msg}[/bold green] 🚀")
    elif score.total >= 70:
        console.print(f"\n[bold blue]{grade_msg}[/bold blue] 🛡️")
    elif score.total >= 50:
        console.print(f"\n[bold yellow]{grade_msg}[/bold yellow] 😬")
    elif score.total >= 25:
        console.print(f"\n[bold orange1]{grade_msg}[/bold orange1] 🍝")
    else:
        console.print(f"\n[bold red]{grade_msg}[/bold red] 🔥")

    console.print("\n" + "=" * 60)
    console.print(score.summary())
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

    # Code smells with roasts
    if result.quality_report and result.quality_report.smells:
        console.print("\n[bold magenta]Code Smells (Gordon Ramsay Mode):[/bold magenta]")
        for smell in result.quality_report.smells[:5]:
            console.print(f"  [magenta]🔥[/magenta] {smell.file.split('/')[-1]}:{smell.line}")
            console.print(f"    [italic]{smell.roast}[/italic]")
            if smell.context:
                console.print(f"    Context: {smell.context}")


if __name__ == "__main__":
    sys.exit(main())
