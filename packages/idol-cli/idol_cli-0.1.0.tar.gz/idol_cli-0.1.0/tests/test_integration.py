"""
Integration tests for the IDOL system.
"""

import json
from pathlib import Path

from click.testing import CliRunner

from idol.cli import cli
from idol.freezer import freeze_task
from idol.harvester import generate_candidates, save_candidates_by_task
from idol.utils import ensure_directories


def test_end_to_end_workflow(temp_dir: Path, sample_debug_trace: Path, monkeypatch):
    """Test complete workflow: harvest -> review -> freeze."""
    monkeypatch.chdir(temp_dir)

    # Step 1: Harvest
    candidates = generate_candidates([sample_debug_trace])
    assert len(candidates) > 0

    counts = save_candidates_by_task(candidates)
    assert "gpu_hw_analysis" in counts

    # Verify candidates file created
    candidates_file = Path("rca_gold/candidates/gpu_hw_analysis.jsonl")
    assert candidates_file.exists()

    # Step 2: Simulate review (mark as accepted)
    candidates_data = []
    with open(candidates_file, "r") as f:
        for line in f:
            candidate = json.loads(line)
            candidate["status"] = "accepted"
            candidates_data.append(candidate)

    with open(candidates_file, "w") as f:
        for c in candidates_data:
            f.write(json.dumps(c) + "\n")

    # Step 3: Freeze
    stats = freeze_task("gpu_hw_analysis")
    assert stats["frozen_records"] > 0

    # Verify frozen file created
    frozen_file = Path("rca_gold/frozen/gpu_hw_analysis.json")
    assert frozen_file.exists()

    with open(frozen_file, "r") as f:
        frozen_data = json.load(f)

    assert len(frozen_data) == stats["frozen_records"]
    assert all("gold" in record for record in frozen_data)


def test_cli_harvest_command(temp_dir: Path, sample_debug_trace: Path, monkeypatch):
    """Test CLI harvest command."""
    monkeypatch.chdir(temp_dir)

    runner = CliRunner()
    result = runner.invoke(cli, ["harvest", str(sample_debug_trace)])

    assert result.exit_code == 0
    assert "Harvesting candidates from" in result.output
    assert "Harvest complete!" in result.output

    # Check that files were created
    candidates_dir = Path("rca_gold/candidates")
    assert candidates_dir.exists()
    assert len(list(candidates_dir.glob("*.jsonl"))) > 0


def test_cli_status_command(temp_dir: Path, monkeypatch):
    """Test CLI status command."""
    monkeypatch.chdir(temp_dir)

    # Create some test data
    ensure_directories()

    # Add candidates
    candidates_file = Path("rca_gold/candidates/test_task.jsonl")
    with open(candidates_file, "w") as f:
        f.write('{"id": "test1", "task": "test_task"}\n')
        f.write('{"id": "test2", "task": "test_task"}\n')

    runner = CliRunner()
    result = runner.invoke(cli, ["status"])

    assert result.exit_code == 0
    assert "IDOL System Status" in result.output
    assert "test_task: 2 candidates" in result.output


def test_cli_freeze_command(temp_dir: Path, monkeypatch):
    """Test CLI freeze command."""
    monkeypatch.chdir(temp_dir)

    # Create test candidates
    ensure_directories()
    candidates_file = Path("rca_gold/candidates/test_task.jsonl")

    candidates = [
        {
            "id": "id1",
            "task": "test_task",
            "input": {"job_id": 1, "attempt": 0, "key_findings": "test"},
            "auto": {"result": "test_result"},
            "status": "accepted",
        }
    ]

    with open(candidates_file, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")

    runner = CliRunner()
    result = runner.invoke(cli, ["freeze", "--task", "test_task"])

    assert result.exit_code == 0
    assert "Freezing datasets" in result.output
    assert "Datasets frozen!" in result.output

    # Check frozen file
    frozen_file = Path("rca_gold/frozen/test_task.json")
    assert frozen_file.exists()


def test_cli_clean_command(temp_dir: Path, monkeypatch):
    """Test CLI clean command."""
    monkeypatch.chdir(temp_dir)

    # Create some data
    ensure_directories()
    test_file = Path("rca_gold/candidates/test.jsonl")
    test_file.write_text("test")

    assert Path("rca_gold").exists()

    runner = CliRunner()
    result = runner.invoke(cli, ["clean"], input="y\n")

    assert result.exit_code == 0
    assert "Cleaned all generated data" in result.output
    assert not Path("rca_gold").exists()


def test_multiple_task_workflow(temp_dir: Path, monkeypatch):
    """Test workflow with multiple tasks."""
    monkeypatch.chdir(temp_dir)

    # Create sample data for multiple tasks
    from idol.models import AutoLabel, CandidateRecord, TaskInput

    candidates = [
        CandidateRecord(
            id="id1",
            task="gpu_hw_analysis",
            input=TaskInput(job_id=1, attempt=0, key_findings="XID 48", tool_calls=[]),
            auto=AutoLabel(result="confirmed_hw_failure"),
            status="pending",
        ),
        CandidateRecord(
            id="id2",
            task="logs_analysis",
            input=TaskInput(job_id=1, attempt=0, key_findings="inf gradient", tool_calls=[]),
            auto=AutoLabel(result="numerical_instability"),
            status="pending",
        ),
        CandidateRecord(
            id="id3",
            task="final_analysis",
            input=TaskInput(job_id=1, attempt=0, key_findings="hardware failure", tool_calls=[]),
            auto=AutoLabel(result="hardware_failure", evidence="confidence=0.9"),
            status="pending",
        ),
    ]

    # Save candidates
    counts = save_candidates_by_task(candidates)
    assert len(counts) == 3

    # Mark as accepted
    for task in ["gpu_hw_analysis", "logs_analysis", "final_analysis"]:
        candidates_file = Path(f"rca_gold/candidates/{task}.jsonl")

        data = []
        with open(candidates_file, "r") as f:
            for line in f:
                record = json.loads(line)
                record["status"] = "accepted"
                data.append(record)

        with open(candidates_file, "w") as f:
            for d in data:
                f.write(json.dumps(d) + "\n")

    # Freeze all tasks
    from idol.freezer import freeze_all_tasks

    all_stats = freeze_all_tasks()

    assert len(all_stats) == 3
    for task, stats in all_stats.items():
        assert "frozen_records" in stats
        assert stats["frozen_records"] == 1

        # Check frozen file exists
        frozen_file = Path(f"rca_gold/frozen/{task}.json")
        assert frozen_file.exists()
