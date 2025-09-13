"""
Freezer module for dataset finalization and validation.
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from idol.utils import read_jsonl


def load_candidates_and_overrides(
    task_name: str,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Load candidates and overrides for a task.

    Args:
        task_name: Name of the task

    Returns:
        Tuple of (candidates dict, overrides dict) keyed by ID
    """
    # Load candidates
    candidates = {}
    candidates_path = Path(f"rca_gold/candidates/{task_name}.jsonl")
    if candidates_path.exists():
        for record in read_jsonl(candidates_path):
            candidates[record["id"]] = record

    # Load overrides
    overrides = {}
    overrides_path = Path(f"rca_gold/overrides/{task_name}.jsonl")
    if overrides_path.exists():
        for record in read_jsonl(overrides_path):
            overrides[record["id"]] = record

    return candidates, overrides


def merge_candidate_with_override(
    candidate: Dict[str, Any], override: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Merge a candidate with its override (if any).

    Args:
        candidate: Candidate record
        override: Override record (or None)

    Returns:
        Merged record with final gold label
    """
    if override:
        # Use the gold label from override
        gold = override["gold"]
    else:
        # Use auto label as gold (for accepted candidates)
        auto = candidate["auto"]

        # Convert auto label to gold label format
        if candidate["task"] == "final_analysis":
            # For final_analysis, we need to extract root_cause and confidence
            gold = {
                "root_cause": auto.get("result", "unknown"),
                "confidence": None,  # Try to extract from evidence
                "evidence": auto.get("evidence"),
            }

            # Try to extract confidence from evidence
            if auto.get("evidence") and "confidence=" in auto["evidence"]:
                try:
                    conf_str = auto["evidence"].split("confidence=")[1].split()[0]
                    gold["confidence"] = float(conf_str)
                except (IndexError, ValueError):
                    gold["confidence"] = 0.5
            else:
                gold["confidence"] = 0.5
        else:
            # For other tasks, just use result
            gold = {"result": auto.get("result", "unknown"), "evidence": auto.get("evidence")}

    return {"id": candidate["id"], "input": candidate["input"], "gold": gold}


def validate_record(record: Dict[str, Any], task_name: str) -> bool:
    """
    Validate a record has required fields based on task type.

    Args:
        record: Record to validate
        task_name: Name of the task

    Returns:
        True if valid, False otherwise
    """
    if not record.get("id") or not record.get("input") or not record.get("gold"):
        return False

    gold = record["gold"]

    if task_name == "final_analysis":
        # Must have root_cause and confidence
        if not gold.get("root_cause"):
            return False
        if gold.get("confidence") is None:
            return False
        # Validate confidence range
        try:
            conf = float(gold["confidence"])
            if not 0 <= conf <= 1:
                return False
        except (TypeError, ValueError):
            return False
    else:
        # Must have result field
        if not gold.get("result"):
            return False

    return True


def split_holdout(
    records: List[Dict[str, Any]], holdout_fraction: float = 0.2, seed: Optional[int] = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split records into train and holdout sets.

    Args:
        records: List of records to split
        holdout_fraction: Fraction to hold out (default 0.2 = 20%)
        seed: Random seed for reproducibility

    Returns:
        Tuple of (train_records, holdout_records)
    """
    if seed is not None:
        random.seed(seed)

    # Shuffle records
    shuffled = records.copy()
    random.shuffle(shuffled)

    # Calculate split point
    holdout_size = int(len(shuffled) * holdout_fraction)

    # Split
    holdout = shuffled[:holdout_size]
    train = shuffled[holdout_size:]

    return train, holdout


def freeze_task(
    task_name: str, validate: bool = True, create_holdout: bool = False
) -> Dict[str, Any]:
    """
    Freeze a task's dataset by merging candidates and overrides.

    Args:
        task_name: Name of the task
        validate: Whether to validate records
        create_holdout: Whether to create a holdout set

    Returns:
        Statistics about the frozen dataset
    """
    print(f"Freezing dataset for task: {task_name}")

    # Load data
    candidates, overrides = load_candidates_and_overrides(task_name)

    if not candidates:
        print(f"No candidates found for task {task_name}")
        return {"error": "No candidates found"}

    print(f"Loaded {len(candidates)} candidates and {len(overrides)} overrides")

    # Merge candidates with overrides
    frozen_records = []
    invalid_count = 0

    for cid, candidate in candidates.items():
        # Skip if not accepted or reviewed
        if candidate.get("status") == "pending":
            continue

        # Merge with override if exists
        override = overrides.get(cid)
        merged = merge_candidate_with_override(candidate, override)

        # Validate if requested
        if validate:
            if validate_record(merged, task_name):
                frozen_records.append(merged)
            else:
                invalid_count += 1
                print(f"Invalid record skipped: {cid}")
        else:
            frozen_records.append(merged)

    if not frozen_records:
        print(f"No valid records to freeze for task {task_name}")
        return {"error": "No valid records"}

    print(f"Prepared {len(frozen_records)} valid records ({invalid_count} invalid skipped)")

    # Split into train/holdout if requested
    if create_holdout and len(frozen_records) >= 5:  # Need at least 5 records to split
        train_records, holdout_records = split_holdout(frozen_records)

        # Write train set
        train_path = Path(f"rca_gold/frozen/{task_name}.json")
        train_path.parent.mkdir(parents=True, exist_ok=True)
        with open(train_path, "w", encoding="utf-8") as f:
            json.dump(train_records, f, indent=2, ensure_ascii=False)

        # Write holdout set
        holdout_path = Path(f"rca_gold/frozen/{task_name}.holdout.json")
        with open(holdout_path, "w", encoding="utf-8") as f:
            json.dump(holdout_records, f, indent=2, ensure_ascii=False)

        print(f"Created train set: {len(train_records)} records")
        print(f"Created holdout set: {len(holdout_records)} records")

        stats = {
            "task": task_name,
            "total_candidates": len(candidates),
            "total_overrides": len(overrides),
            "frozen_records": len(frozen_records),
            "invalid_skipped": invalid_count,
            "train_size": len(train_records),
            "holdout_size": len(holdout_records),
        }
    else:
        # Write all records to single file
        output_path = Path(f"rca_gold/frozen/{task_name}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(frozen_records, f, indent=2, ensure_ascii=False)

        print(f"Frozen dataset written to: {output_path}")

        stats = {
            "task": task_name,
            "total_candidates": len(candidates),
            "total_overrides": len(overrides),
            "frozen_records": len(frozen_records),
            "invalid_skipped": invalid_count,
        }

    return stats


def freeze_all_tasks(validate: bool = True, create_holdout: bool = False) -> Dict[str, Any]:
    """
    Freeze datasets for all tasks that have candidates.

    Args:
        validate: Whether to validate records
        create_holdout: Whether to create holdout sets

    Returns:
        Statistics for all tasks
    """
    candidates_dir = Path("rca_gold/candidates")

    if not candidates_dir.exists():
        print("No candidates directory found")
        return {}

    all_stats = {}

    # Process each task file
    for jsonl_file in candidates_dir.glob("*.jsonl"):
        task_name = jsonl_file.stem  # Remove .jsonl extension
        stats = freeze_task(task_name, validate, create_holdout)
        all_stats[task_name] = stats

    return all_stats
