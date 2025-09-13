"""
Tests for the freezer module.
"""

import json
from pathlib import Path

from idol.freezer import (
    freeze_task,
    merge_candidate_with_override,
    split_holdout,
    validate_record,
)


def test_validate_record():
    """Test record validation."""
    # Valid non-final task record
    record = {"id": "test123", "input": {"job_id": 1, "attempt": 0}, "gold": {"result": "no_issue"}}
    assert validate_record(record, "gpu_hw_analysis") is True

    # Invalid - missing result
    record["gold"] = {}
    assert validate_record(record, "gpu_hw_analysis") is False

    # Valid final_analysis record
    record = {
        "id": "test456",
        "input": {"job_id": 1, "attempt": 0},
        "gold": {"root_cause": "hardware_failure", "confidence": 0.9},
    }
    assert validate_record(record, "final_analysis") is True

    # Invalid final_analysis - missing confidence
    record["gold"] = {"root_cause": "hardware_failure"}
    assert validate_record(record, "final_analysis") is False

    # Invalid final_analysis - confidence out of range
    record["gold"] = {"root_cause": "hardware_failure", "confidence": 1.5}
    assert validate_record(record, "final_analysis") is False


def test_merge_candidate_with_override():
    """Test merging candidate with override."""
    candidate = {
        "id": "test123",
        "task": "gpu_hw_analysis",
        "input": {"job_id": 1},
        "auto": {"result": "no_hw_issue", "evidence": "auto"},
    }

    # Without override - use auto label
    merged = merge_candidate_with_override(candidate, None)
    assert merged["gold"]["result"] == "no_hw_issue"

    # With override - use override label
    override = {"id": "test123", "gold": {"result": "confirmed_hw_failure", "evidence": "manual"}}
    merged = merge_candidate_with_override(candidate, override)
    assert merged["gold"]["result"] == "confirmed_hw_failure"
    assert merged["gold"]["evidence"] == "manual"


def test_merge_final_analysis():
    """Test merging final_analysis task."""
    candidate = {
        "id": "test789",
        "task": "final_analysis",
        "input": {"job_id": 1},
        "auto": {"result": "hardware_failure", "evidence": "confidence=0.8"},
    }

    # Should extract confidence from evidence
    merged = merge_candidate_with_override(candidate, None)
    assert merged["gold"]["root_cause"] == "hardware_failure"
    assert merged["gold"]["confidence"] == 0.8


def test_split_holdout():
    """Test train/holdout split."""
    records = [{"id": str(i)} for i in range(100)]

    train, holdout = split_holdout(records, holdout_fraction=0.2, seed=42)

    assert len(train) == 80
    assert len(holdout) == 20

    # Check no overlap
    train_ids = {r["id"] for r in train}
    holdout_ids = {r["id"] for r in holdout}
    assert train_ids.isdisjoint(holdout_ids)

    # Check deterministic with same seed
    train2, holdout2 = split_holdout(records, holdout_fraction=0.2, seed=42)
    assert train == train2
    assert holdout == holdout2


def test_freeze_task_no_candidates(temp_dir: Path, monkeypatch):
    """Test freezing with no candidates."""
    monkeypatch.chdir(temp_dir)

    stats = freeze_task("nonexistent_task")
    assert "error" in stats
    assert stats["error"] == "No candidates found"


def test_freeze_task_with_candidates(temp_dir: Path, monkeypatch):
    """Test freezing with candidates."""
    monkeypatch.chdir(temp_dir)

    # Create candidates file
    candidates_dir = temp_dir / "rca_gold" / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)

    candidates = [
        {
            "id": "id1",
            "task": "gpu_hw_analysis",
            "input": {"job_id": 1, "attempt": 0, "key_findings": "test"},
            "auto": {"result": "no_hw_issue"},
            "status": "accepted",
        },
        {
            "id": "id2",
            "task": "gpu_hw_analysis",
            "input": {"job_id": 2, "attempt": 0, "key_findings": "test2"},
            "auto": {"result": "confirmed_hw_failure"},
            "status": "accepted",
        },
        {
            "id": "id3",
            "task": "gpu_hw_analysis",
            "input": {"job_id": 3, "attempt": 0, "key_findings": "test3"},
            "auto": {"result": "no_hw_issue"},
            "status": "pending",  # Should be skipped
        },
    ]

    candidates_file = candidates_dir / "gpu_hw_analysis.jsonl"
    with open(candidates_file, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")

    # Freeze without holdout
    stats = freeze_task("gpu_hw_analysis", validate=True, create_holdout=False)

    assert stats["total_candidates"] == 3
    assert stats["frozen_records"] == 2  # Only accepted ones

    # Check output file
    frozen_file = temp_dir / "rca_gold" / "frozen" / "gpu_hw_analysis.json"
    assert frozen_file.exists()

    with open(frozen_file) as f:
        frozen_data = json.load(f)

    assert len(frozen_data) == 2
    assert all("gold" in r for r in frozen_data)


def test_freeze_task_with_holdout(temp_dir: Path, monkeypatch):
    """Test freezing with holdout split."""
    monkeypatch.chdir(temp_dir)

    # Create candidates file with enough records for split
    candidates_dir = temp_dir / "rca_gold" / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)

    candidates = []
    for i in range(10):
        candidates.append(
            {
                "id": f"id{i}",
                "task": "gpu_hw_analysis",
                "input": {"job_id": i, "attempt": 0, "key_findings": f"test{i}"},
                "auto": {"result": "no_hw_issue"},
                "status": "accepted",
            }
        )

    candidates_file = candidates_dir / "gpu_hw_analysis.jsonl"
    with open(candidates_file, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")

    # Freeze with holdout
    stats = freeze_task("gpu_hw_analysis", validate=True, create_holdout=True)

    assert "train_size" in stats
    assert "holdout_size" in stats
    assert stats["train_size"] + stats["holdout_size"] == 10

    # Check output files
    train_file = temp_dir / "rca_gold" / "frozen" / "gpu_hw_analysis.json"
    holdout_file = temp_dir / "rca_gold" / "frozen" / "gpu_hw_analysis.holdout.json"

    assert train_file.exists()
    assert holdout_file.exists()
