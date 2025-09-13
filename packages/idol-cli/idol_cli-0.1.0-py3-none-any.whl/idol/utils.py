"""
Utility functions for IDOL system.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional


def generate_stable_id(job_id: int, attempt: int, task: str, key_findings: str) -> str:
    """
    Generate deterministic ID using SHA1.

    Args:
        job_id: Job identifier
        attempt: Attempt number
        task: Task name
        key_findings: Key findings text (first 200 chars used)

    Returns:
        SHA1 hash hex string
    """
    # Use first 200 chars of key_findings for stability
    truncated_findings = key_findings[:200] if key_findings else ""
    content = f"{job_id}|{attempt}|{task}|{truncated_findings}"
    return hashlib.sha1(content.encode("utf-8")).hexdigest()


def read_jsonl(filepath: Path) -> Generator[Dict[str, Any], None, None]:
    """
    Stream JSONL file line by line.

    Args:
        filepath: Path to JSONL file

    Yields:
        Parsed JSON objects
    """
    if not filepath.exists():
        return

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():  # Skip empty lines
                yield json.loads(line)


def write_jsonl(filepath: Path, records: List[Dict[str, Any]], append: bool = True) -> None:
    """
    Write records to JSONL file atomically.

    Args:
        filepath: Path to write to
        records: List of records to write
        append: Whether to append to existing file
    """
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file first for atomicity
    temp_path = filepath.with_suffix(".tmp")

    if append and filepath.exists():
        # Copy existing content to temp file
        with open(filepath, "r", encoding="utf-8") as src:
            with open(temp_path, "w", encoding="utf-8") as dst:
                dst.write(src.read())
        mode = "a"
    else:
        mode = "w"

    # Write new records
    with open(temp_path, mode, encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    # Atomic rename
    temp_path.replace(filepath)


def ensure_directories() -> None:
    """Create necessary data directories if they don't exist."""
    directories = [
        Path("rca_gold/candidates"),
        Path("rca_gold/overrides"),
        Path("rca_gold/frozen"),
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def load_existing_ids(task: Optional[str] = None) -> set[str]:
    """
    Load existing candidate IDs to avoid duplicates.

    Args:
        task: Optional task name to filter by

    Returns:
        Set of existing IDs
    """
    existing_ids: set[str] = set()
    candidates_dir = Path("rca_gold/candidates")

    if not candidates_dir.exists():
        return existing_ids

    if task:
        # Load IDs from specific task file
        task_file = candidates_dir / f"{task}.jsonl"
        if task_file.exists():
            for record in read_jsonl(task_file):
                record_id = record.get("id")
                if record_id:
                    existing_ids.add(record_id)
    else:
        # Load IDs from all task files
        for jsonl_file in candidates_dir.glob("*.jsonl"):
            for record in read_jsonl(jsonl_file):
                record_id = record.get("id")
                if record_id:
                    existing_ids.add(record_id)

    return existing_ids
