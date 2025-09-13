"""
Harvester module for generating candidates from debug traces.
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Generator, List

from idol.heuristics import apply_heuristic
from idol.models import CandidateRecord, TaskInput, ToolCall
from idol.utils import generate_stable_id, load_existing_ids, write_jsonl


def parse_debug_trace(trace_path: Path) -> Generator[Dict[str, Any], None, None]:
    """
    Extract task executions from debug trace JSON files.

    The debug traces contain information about task executions with key_findings.
    We need to extract the job_id, attempt, task name, and key_findings.

    Args:
        trace_path: Path to debug trace JSON file

    Yields:
        Task execution dictionaries
    """
    try:
        # Read the entire JSON file (since these aren't too large based on examples)
        with open(trace_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Skip if data is a list (tool_calls files)
        if isinstance(data, list):
            return

        # Skip if no messages_sent (not a trace file)
        if not isinstance(data, dict) or "messages_sent" not in data:
            return

        # Extract task name from the user message if present
        task_name = None
        job_id = 4824587  # Default from examples
        attempt = 0  # Default attempt

        # Parse messages to find task info
        messages = data.get("messages_sent", [])
        for msg in messages:
            content = msg.get("content", "")

            # Handle case where content is a list (new format)
            if isinstance(content, list):
                # Extract text from content list
                text_parts = []
                for content_item in content:
                    if isinstance(content_item, dict) and content_item.get("type") == "text":
                        text_parts.append(content_item.get("text", ""))
                content = " ".join(text_parts)

            # Skip if content is not a string
            if not isinstance(content, str):
                continue

            # Try to extract task name from various patterns
            if "TASK_COMPLETE:" in content:
                # Extract task name from completion marker
                match = re.search(r"TASK_COMPLETE:\s*(\w+)", content)
                if match:
                    task_name = match.group(1)

            # Try to extract job_id
            job_match = re.search(r'job_id[=:]\s*[\'"]?(\d+)', content, re.IGNORECASE)
            if job_match:
                job_id = int(job_match.group(1))

            # Try to extract attempt
            attempt_match = re.search(r"attempt[=:]\s*(\d+)", content, re.IGNORECASE)
            if attempt_match:
                attempt = int(attempt_match.group(1))

        # Look for KEY_FINDINGS in the response
        key_findings = ""
        data.get("response_text", "")

        # Check in final_message content
        final_message = data.get("final_message", {})
        content_items = final_message.get("content", [])

        # Handle case where content is not a list
        if not isinstance(content_items, list):
            content_items = []

        for content_item in content_items:
            if isinstance(content_item, dict) and content_item.get("type") == "text":
                text = content_item.get("text", "")
                if "KEY_FINDINGS" in text:
                    # Extract everything after KEY_FINDINGS
                    parts = text.split("KEY_FINDINGS", 1)
                    if len(parts) > 1:
                        findings_part = parts[1]
                        # Extract until TASK_COMPLETE
                        if "TASK_COMPLETE" in findings_part:
                            key_findings = findings_part.split("TASK_COMPLETE")[0].strip()
                            # Also extract task name from TASK_COMPLETE
                            tc_match = re.search(r"TASK_COMPLETE:\s*(\w+)", findings_part)
                            if tc_match:
                                task_name = tc_match.group(1)
                        else:
                            key_findings = findings_part.strip()

                        # Clean up the key_findings
                        key_findings = key_findings.strip(":").strip()

        # Extract tool calls
        tool_calls = []
        tool_results = data.get("tool_results", [])

        # Extract tool call information from final_message
        for content_item in final_message.get("content", []):
            if content_item.get("type") == "tool_use":
                tool_call = ToolCall(
                    name=content_item.get("name", ""), args=content_item.get("input", {})
                )
                tool_calls.append(tool_call)

        # If we found a task execution with key findings, yield it
        if task_name and key_findings:
            yield {
                "job_id": job_id,
                "attempt": attempt,
                "task": task_name,
                "key_findings": key_findings,
                "tool_calls": tool_calls,
                "tool_results": tool_results,
            }

    except Exception as e:
        print(f"Error parsing {trace_path}: {e}")


def parse_final_results(results_path: Path) -> Generator[Dict[str, Any], None, None]:
    """
    Parse final_results.json file which has a different structure.

    Args:
        results_path: Path to final_results.json

    Yields:
        Task execution dictionaries
    """
    try:
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Default job info
        job_id = 4824587
        attempt = 0

        # Extract task results
        task_results = data.get("final_analysis", {}).get("task_results", {})

        for task_name, task_data in task_results.items():
            if task_data.get("success") and task_data.get("key_findings"):
                yield {
                    "job_id": job_id,
                    "attempt": attempt,
                    "task": task_name,
                    "key_findings": task_data["key_findings"],
                    "tool_calls": [],  # Not available in final_results
                    "tool_results": [],
                }

        # Also check for final_analysis at top level
        if data.get("final_analysis", {}).get("final_analysis"):
            yield {
                "job_id": job_id,
                "attempt": attempt,
                "task": "final_analysis",
                "key_findings": data["final_analysis"]["final_analysis"],
                "tool_calls": [],
                "tool_results": [],
            }

    except Exception as e:
        print(f"Error parsing {results_path}: {e}")


def generate_candidates(trace_files: List[Path]) -> List[CandidateRecord]:
    """
    Generate candidate records from debug trace files.

    Args:
        trace_files: List of paths to debug trace JSON files

    Returns:
        List of CandidateRecord objects
    """
    candidates = []
    existing_ids = load_existing_ids()

    for trace_file in trace_files:
        # Determine parser based on filename
        if "final_results" in trace_file.name:
            task_generator = parse_final_results(trace_file)
        else:
            task_generator = parse_debug_trace(trace_file)

        for task_exec in task_generator:
            # Generate stable ID
            candidate_id = generate_stable_id(
                task_exec["job_id"],
                task_exec["attempt"],
                task_exec["task"],
                task_exec["key_findings"],
            )

            # Skip if already exists (idempotency)
            if candidate_id in existing_ids:
                continue

            # Apply heuristic to generate auto label
            auto_label = apply_heuristic(
                task_exec["task"], task_exec["key_findings"], task_exec.get("tool_results", [])
            )

            # Create candidate record
            try:
                candidate = CandidateRecord(
                    id=candidate_id,
                    task=task_exec["task"],
                    input=TaskInput(
                        job_id=task_exec["job_id"],
                        attempt=task_exec["attempt"],
                        key_findings=task_exec["key_findings"],
                        tool_calls=task_exec.get("tool_calls", []),
                    ),
                    auto=auto_label,
                    status="pending",
                )
                candidates.append(candidate)
            except Exception as e:
                print(f"Error creating candidate: {e}")

    return candidates


def save_candidates_by_task(candidates: List[CandidateRecord]) -> Dict[str, int]:
    """
    Save candidates grouped by task to JSONL files.

    Args:
        candidates: List of candidate records

    Returns:
        Dictionary mapping task names to count of candidates saved
    """
    # Group candidates by task
    by_task = defaultdict(list)
    for candidate in candidates:
        by_task[candidate.task].append(candidate)

    # Save each task's candidates
    counts = {}
    for task_name, task_candidates in by_task.items():
        output_path = Path(f"rca_gold/candidates/{task_name}.jsonl")

        # Convert to dictionaries for JSON serialization
        records = [c.model_dump() for c in task_candidates]

        # Write to JSONL file
        write_jsonl(output_path, records, append=True)
        counts[task_name] = len(task_candidates)

    return counts
