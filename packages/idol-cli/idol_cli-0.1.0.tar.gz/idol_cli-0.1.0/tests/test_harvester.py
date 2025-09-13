"""
Tests for the harvester module.
"""

from pathlib import Path

from idol.harvester import (
    generate_candidates,
    parse_debug_trace,
    parse_final_results,
    save_candidates_by_task,
)
from idol.utils import generate_stable_id


def test_stable_id_generation():
    """Test that ID generation is deterministic."""
    id1 = generate_stable_id(123, 0, "task", "findings")
    id2 = generate_stable_id(123, 0, "task", "findings")
    assert id1 == id2

    # Different inputs should produce different IDs
    id3 = generate_stable_id(124, 0, "task", "findings")
    assert id1 != id3


def test_stable_id_truncation():
    """Test that key_findings are truncated at 200 chars."""
    long_findings = "x" * 300
    id1 = generate_stable_id(123, 0, "task", long_findings)

    # Should be same as using first 200 chars
    id2 = generate_stable_id(123, 0, "task", "x" * 200)
    assert id1 == id2

    # But different from 199 chars
    id3 = generate_stable_id(123, 0, "task", "x" * 199)
    assert id1 != id3


def test_parse_debug_trace(sample_debug_trace: Path):
    """Test parsing a debug trace file."""
    results = list(parse_debug_trace(sample_debug_trace))

    assert len(results) == 1
    result = results[0]

    assert result["job_id"] == 4824587
    assert result["attempt"] == 0
    assert result["task"] == "gpu_hw_analysis"
    assert "XID 48" in result["key_findings"]


def test_parse_final_results(sample_final_results: Path):
    """Test parsing a final_results.json file."""
    results = list(parse_final_results(sample_final_results))

    assert len(results) == 2

    # Check first result
    gpu_result = next(r for r in results if r["task"] == "gpu_hw_analysis")
    assert gpu_result["key_findings"] == "No GPU hardware failures detected"

    # Check second result
    logs_result = next(r for r in results if r["task"] == "logs_analysis")
    assert "inf gradient" in logs_result["key_findings"]


def test_generate_candidates(sample_debug_trace: Path, sample_final_results: Path):
    """Test generating candidates from multiple files."""
    candidates = generate_candidates([sample_debug_trace, sample_final_results])

    assert len(candidates) >= 2  # At least one from each file

    # Check that candidates have required fields
    for candidate in candidates:
        assert candidate.id
        assert candidate.task
        assert candidate.input
        assert candidate.auto
        assert candidate.status == "pending"


def test_idempotent_harvest(sample_debug_trace: Path, temp_dir: Path, monkeypatch):
    """Test that re-running harvest doesn't create duplicates."""
    # Set working directory to temp_dir for isolated testing
    monkeypatch.chdir(temp_dir)

    # Run harvest twice
    candidates1 = generate_candidates([sample_debug_trace])
    save_candidates_by_task(candidates1)

    candidates2 = generate_candidates([sample_debug_trace])

    # Second run should not generate any new candidates
    assert len(candidates2) == 0  # All filtered as duplicates


def test_save_candidates_by_task(temp_dir: Path, monkeypatch):
    """Test saving candidates grouped by task."""
    from idol.models import AutoLabel, CandidateRecord, TaskInput

    # Set working directory
    monkeypatch.chdir(temp_dir)

    # Create candidates for different tasks
    candidates = [
        CandidateRecord(
            id="id1",
            task="gpu_hw_analysis",
            input=TaskInput(job_id=1, attempt=0, key_findings="test1", tool_calls=[]),
            auto=AutoLabel(result="no_hw_issue"),
            status="pending",
        ),
        CandidateRecord(
            id="id2",
            task="gpu_hw_analysis",
            input=TaskInput(job_id=2, attempt=0, key_findings="test2", tool_calls=[]),
            auto=AutoLabel(result="confirmed_hw_failure"),
            status="pending",
        ),
        CandidateRecord(
            id="id3",
            task="logs_analysis",
            input=TaskInput(job_id=3, attempt=0, key_findings="test3", tool_calls=[]),
            auto=AutoLabel(result="no_issue"),
            status="pending",
        ),
    ]

    counts = save_candidates_by_task(candidates)

    assert counts["gpu_hw_analysis"] == 2
    assert counts["logs_analysis"] == 1

    # Check files were created
    gpu_file = Path("rca_gold/candidates/gpu_hw_analysis.jsonl")
    logs_file = Path("rca_gold/candidates/logs_analysis.jsonl")

    assert gpu_file.exists()
    assert logs_file.exists()

    # Check content
    with open(gpu_file) as f:
        lines = f.readlines()
    assert len(lines) == 2

    with open(logs_file) as f:
        lines = f.readlines()
    assert len(lines) == 1
