"""
Reviewer module for human validation of candidates.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from idol.models import GoldLabel, OverrideRecord
from idol.utils import read_jsonl, write_jsonl


def load_pending_candidates(task_name: str) -> List[Dict[str, Any]]:
    """
    Load pending candidates for a specific task.

    Args:
        task_name: Name of the task

    Returns:
        List of pending candidate dictionaries
    """
    candidates_path = Path(f"rca_gold/candidates/{task_name}.jsonl")

    if not candidates_path.exists():
        return []

    # Load all candidates and filter for pending ones
    pending = []
    for candidate in read_jsonl(candidates_path):
        if candidate.get("status") == "pending":
            pending.append(candidate)

    return pending


def load_reviewed_ids(task_name: str) -> set[str]:
    """
    Load IDs that have already been reviewed (have overrides).

    Args:
        task_name: Name of the task

    Returns:
        Set of reviewed candidate IDs
    """
    overrides_path = Path(f"rca_gold/overrides/{task_name}.jsonl")

    if not overrides_path.exists():
        return set()

    reviewed: set[str] = set()
    for override in read_jsonl(overrides_path):
        override_id = override.get("id")
        if override_id:
            reviewed.add(override_id)

    return reviewed


def display_candidate(candidate: Dict[str, Any], index: int, total: int) -> None:
    """
    Display a candidate for review.

    Args:
        candidate: Candidate dictionary
        index: Current index (1-based)
        total: Total number of candidates
    """
    print(f"\n{'=' * 60}")
    print(f"Candidate {index}/{total}")
    print(f"Task: {candidate['task']}")
    print(f"Job ID: {candidate['input']['job_id']}, Attempt: {candidate['input']['attempt']}")
    print("-" * 60)

    # Display key findings (truncate if too long)
    key_findings = candidate["input"]["key_findings"]
    if len(key_findings) > 500:
        print(f"Key Findings (truncated):\n{key_findings[:500]}...")
    else:
        print(f"Key Findings:\n{key_findings}")

    print("-" * 60)
    print(f"Auto Label: {json.dumps(candidate['auto'], indent=2)}")
    print("-" * 60)


def get_user_choice() -> str:
    """
    Get user's choice for the current candidate.

    Returns:
        User's choice character
    """
    print("\nOptions:")
    print("  [a] Accept auto label")
    print("  [n] Negate (mark as 'no_issue')")
    print("  [e] Edit (provide custom JSON)")
    print("  [s] Skip")
    print("  [q] Quit")

    while True:
        choice = input("\nYour choice: ").strip().lower()
        if choice in ["a", "n", "e", "s", "q"]:
            return choice
        print("Invalid choice. Please enter a, n, e, s, or q.")


def get_custom_gold_label(task_name: str) -> Optional[GoldLabel]:
    """
    Get custom gold label from user input.

    Args:
        task_name: Name of the task (for context)

    Returns:
        GoldLabel object or None if invalid
    """
    print("\nEnter custom gold label JSON.")

    if task_name == "final_analysis":
        print('Format: {"root_cause": "...", "confidence": 0.X, "evidence": "..."}')
    else:
        print('Format: {"result": "...", "evidence": "..."}')

    print("(Press Enter on empty line to cancel)")

    json_lines: list[str] = []
    while True:
        line = input()
        if not line and not json_lines:
            return None  # Cancelled
        if not line:
            break
        json_lines.append(line)

    json_str = "\n".join(json_lines)

    try:
        gold_data = json.loads(json_str)
        return GoldLabel(**gold_data)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Invalid JSON or format: {e}")
        return None


def save_override(task_name: str, candidate_id: str, gold: GoldLabel, note: str) -> None:
    """
    Save an override for a candidate.

    Args:
        task_name: Name of the task
        candidate_id: ID of the candidate
        gold: Gold label to save
        note: Note about the override
    """
    override = OverrideRecord(id=candidate_id, gold=gold, note=note)

    overrides_path = Path(f"rca_gold/overrides/{task_name}.jsonl")
    write_jsonl(overrides_path, [override.model_dump()], append=True)


def update_candidate_status(task_name: str, candidate_id: str, new_status: str) -> None:
    """
    Update the status of a candidate in the candidates file.

    Args:
        task_name: Name of the task
        candidate_id: ID of the candidate
        new_status: New status value
    """
    candidates_path = Path(f"rca_gold/candidates/{task_name}.jsonl")

    # Read all candidates
    all_candidates = list(read_jsonl(candidates_path))

    # Update the status
    for candidate in all_candidates:
        if candidate.get("id") == candidate_id:
            candidate["status"] = new_status

    # Write back (not appending, replacing)
    write_jsonl(candidates_path, all_candidates, append=False)


def review_task(task_name: str, max_items: Optional[int] = None) -> None:
    """
    Interactive review interface for a specific task.

    Args:
        task_name: Name of the task to review
        max_items: Maximum number of items to review (None for all)
    """
    print(f"\n=== Reviewing task: {task_name} ===")

    # Load pending candidates
    pending = load_pending_candidates(task_name)

    # Filter out already reviewed ones
    reviewed_ids = load_reviewed_ids(task_name)
    pending = [c for c in pending if c.get("id") not in reviewed_ids]

    if not pending:
        print("No pending candidates to review.")
        return

    print(f"Found {len(pending)} pending candidates.")

    if max_items:
        pending = pending[:max_items]
        print(f"Reviewing first {max_items} candidates.")

    # Review each candidate
    for index, candidate in enumerate(pending, 1):
        display_candidate(candidate, index, len(pending))

        choice = get_user_choice()

        if choice == "q":
            print("\nQuitting review session.")
            break
        elif choice == "s":
            print("Skipped.")
            continue
        elif choice == "a":
            # Accept auto label
            update_candidate_status(task_name, candidate["id"], "accepted")
            print("✓ Auto label accepted.")
        elif choice == "n":
            # Negate - mark as no_issue
            gold = GoldLabel(result="no_issue")
            save_override(task_name, candidate["id"], gold, "manual negation")
            update_candidate_status(task_name, candidate["id"], "reviewed")
            print("✓ Marked as 'no_issue'.")
        elif choice == "e":
            # Custom edit
            custom_gold = get_custom_gold_label(task_name)
            if custom_gold is not None:
                save_override(task_name, candidate["id"], custom_gold, "manual edit")
                update_candidate_status(task_name, candidate["id"], "reviewed")
                print("✓ Custom label saved.")
            else:
                print("Custom label cancelled.")

    print(f"\nReview session completed. Reviewed {index}/{len(pending)} candidates.")
