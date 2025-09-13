"""
CLI interface for IDOL system.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from idol.freezer import freeze_all_tasks, freeze_task
from idol.harvester import generate_candidates, save_candidates_by_task
from idol.reviewer import review_task
from idol.utils import ensure_directories


@click.group()
@click.version_option(version="0.1.0", prog_name="IDOL")
def cli() -> None:
    """IDOL - Incremental DAG Optimization for Learning CLI.

    Transform debug traces into validated golden datasets through:

    \b
    1. harvest: Generate candidate labels from debug traces
    2. review: Interactively validate/correct labels
    3. freeze: Create final validated datasets
    """
    pass


@cli.command()
@click.argument("trace_path", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def harvest(trace_path: str, verbose: bool) -> None:
    """Generate candidates from debug traces.

    TRACE_PATH can be a single JSON file or a directory containing multiple files.
    """
    click.echo(f"🌾 Harvesting candidates from: {trace_path}")

    # Ensure directories exist
    ensure_directories()

    # Determine if path is file or directory
    path = Path(trace_path)
    if path.is_dir():
        # Get all JSON files in directory
        trace_files = list(path.glob("*.json"))
        if not trace_files:
            click.echo(f"❌ No JSON files found in {trace_path}", err=True)
            sys.exit(1)
        click.echo(f"Found {len(trace_files)} JSON files")
    else:
        trace_files = [path]

    # Generate candidates
    if verbose:
        click.echo("Parsing debug traces...")

    candidates = generate_candidates(trace_files)

    if not candidates:
        click.echo("⚠️  No candidates generated. Check that files contain valid task data.")
        return

    click.echo(f"Generated {len(candidates)} candidates")

    # Save candidates by task
    counts = save_candidates_by_task(candidates)

    # Display results
    click.echo("\n📊 Candidates by task:")
    for task_name, count in sorted(counts.items()):
        click.echo(f"  • {task_name}: {count} candidates")

    click.echo("\n✅ Harvest complete! Candidates saved to rca_gold/candidates/")


@cli.command()
@click.option(
    "--task", "-t", required=True, help="Task to review (e.g., gpu_hw_analysis, logs_analysis)"
)
@click.option("--max-items", "-n", type=int, help="Maximum number of items to review")
def review(task: str, max_items: Optional[int]) -> None:
    """Interactive review interface for validating candidates.

    Review pending candidates for a specific task and provide corrections.

    \b
    Available actions:
      [a] Accept auto label
      [n] Negate (mark as 'no_issue')
      [e] Edit (provide custom JSON)
      [s] Skip
      [q] Quit
    """
    click.echo(f"👀 Starting review for task: {task}")

    # Ensure directories exist
    ensure_directories()

    # Check if task has candidates
    candidates_path = Path(f"rca_gold/candidates/{task}.jsonl")
    if not candidates_path.exists():
        click.echo(f"❌ No candidates found for task '{task}'", err=True)
        click.echo("\nAvailable tasks:")

        candidates_dir = Path("rca_gold/candidates")
        if candidates_dir.exists():
            for jsonl_file in candidates_dir.glob("*.jsonl"):
                click.echo(f"  • {jsonl_file.stem}")

        sys.exit(1)

    # Start review
    review_task(task, max_items)

    click.echo("\n✅ Review session completed!")


@cli.command()
@click.option("--task", "-t", help="Task to freeze (omit for all tasks)")
@click.option("--validate/--no-validate", default=True, help="Validate records before freezing")
@click.option("--holdout", is_flag=True, help="Create 80/20 train/holdout split")
def freeze(task: Optional[str], validate: bool, holdout: bool) -> None:
    """Freeze validated dataset for training.

    Merge candidates and overrides into final frozen datasets.
    Invalid records are skipped if validation is enabled.
    """
    click.echo("❄️  Freezing datasets...")

    # Ensure directories exist
    ensure_directories()

    if task:
        # Freeze specific task
        stats = freeze_task(task, validate, holdout)

        if "error" in stats:
            click.echo(f"❌ {stats['error']}", err=True)
            sys.exit(1)

        click.echo(f"\n📊 Freeze statistics for {task}:")
        click.echo(f"  • Total candidates: {stats['total_candidates']}")
        click.echo(f"  • Total overrides: {stats['total_overrides']}")
        click.echo(f"  • Frozen records: {stats['frozen_records']}")

        if validate:
            click.echo(f"  • Invalid skipped: {stats['invalid_skipped']}")

        if holdout and "train_size" in stats:
            click.echo(f"  • Train size: {stats['train_size']}")
            click.echo(f"  • Holdout size: {stats['holdout_size']}")
    else:
        # Freeze all tasks
        all_stats = freeze_all_tasks(validate, holdout)

        if not all_stats:
            click.echo("❌ No tasks found to freeze", err=True)
            sys.exit(1)

        click.echo("\n📊 Freeze statistics for all tasks:")

        total_frozen = 0
        for task_name, stats in sorted(all_stats.items()):
            if "error" not in stats:
                click.echo(f"\n  {task_name}:")
                click.echo(f"    • Frozen records: {stats['frozen_records']}")
                total_frozen += stats["frozen_records"]

                if holdout and "train_size" in stats:
                    click.echo(
                        f"    • Train/Holdout: {stats['train_size']}/{stats['holdout_size']}"
                    )

        click.echo(f"\n  Total frozen records: {total_frozen}")

    click.echo("\n✅ Datasets frozen! Output saved to rca_gold/frozen/")


@cli.command()
def status() -> None:
    """Show current status of candidates, overrides, and frozen datasets."""
    click.echo("📈 IDOL System Status\n")

    # Check candidates
    candidates_dir = Path("rca_gold/candidates")
    if candidates_dir.exists():
        click.echo("📝 Candidates:")
        total_candidates = 0
        for jsonl_file in sorted(candidates_dir.glob("*.jsonl")):
            # Count lines in file
            with open(jsonl_file, "r") as f:
                count = sum(1 for _ in f)
            click.echo(f"  • {jsonl_file.stem}: {count} candidates")
            total_candidates += count
        click.echo(f"  Total: {total_candidates} candidates\n")
    else:
        click.echo("📝 Candidates: None found\n")

    # Check overrides
    overrides_dir = Path("rca_gold/overrides")
    if overrides_dir.exists():
        click.echo("✏️  Overrides:")
        total_overrides = 0
        for jsonl_file in sorted(overrides_dir.glob("*.jsonl")):
            with open(jsonl_file, "r") as f:
                count = sum(1 for _ in f)
            click.echo(f"  • {jsonl_file.stem}: {count} overrides")
            total_overrides += count
        click.echo(f"  Total: {total_overrides} overrides\n")
    else:
        click.echo("✏️  Overrides: None found\n")

    # Check frozen datasets
    frozen_dir = Path("rca_gold/frozen")
    if frozen_dir.exists():
        click.echo("❄️  Frozen Datasets:")
        for json_file in sorted(frozen_dir.glob("*.json")):
            # Get file size
            size_kb = json_file.stat().st_size / 1024
            if ".holdout" in json_file.name:
                click.echo(f"  • {json_file.name}: {size_kb:.1f} KB (holdout)")
            else:
                click.echo(f"  • {json_file.name}: {size_kb:.1f} KB")
    else:
        click.echo("❄️  Frozen Datasets: None found")


@cli.command()
def clean() -> None:
    """Clean all generated data (candidates, overrides, frozen)."""
    click.confirm("⚠️  This will delete all generated data. Continue?", abort=True)

    import shutil

    rca_gold_dir = Path("rca_gold")
    if rca_gold_dir.exists():
        shutil.rmtree(rca_gold_dir)
        click.echo("✅ Cleaned all generated data")
    else:
        click.echo("ℹ️  No data to clean")


if __name__ == "__main__":
    cli()
