"""
Heuristics engine for auto-labeling tasks.
"""

import re
from typing import Any, Dict, List

from idol.models import AutoLabel


def gpu_hw_analysis_heuristic(key_findings: str, tool_results: List[Dict[str, Any]]) -> AutoLabel:
    """
    Determine GPU hardware failure status.

    XIDs that confirm hardware failure vs those that are unconfirmed.
    """
    # CRITICAL XIDs that confirm hardware failure
    confirmed_xids = {46, 48, 62, 64, 79, 95, 110, 119, 120, 136, 140, 143, 149, 155, 156, 158, 159}
    unconfirmed_xids = {31, 94, 137}

    # Search for XID patterns in findings
    xid_pattern = r"XID[- ]?(\d+)"
    xids_found = set()
    for match in re.finditer(xid_pattern, key_findings, re.IGNORECASE):
        xids_found.add(int(match.group(1)))

    # Also look for SXID patterns
    sxid_pattern = r"SXID[- ]?(\d+)"
    for match in re.finditer(sxid_pattern, key_findings, re.IGNORECASE):
        # SXID errors are generally hardware-related
        return AutoLabel(result="confirmed_hw_failure", evidence=f"SXID-{match.group(1)} detected")

    if xids_found & confirmed_xids:
        return AutoLabel(
            result="confirmed_hw_failure", evidence=f"XIDs: {sorted(xids_found & confirmed_xids)}"
        )
    elif xids_found & unconfirmed_xids:
        return AutoLabel(
            result="unconfirmed_xids", evidence=f"XIDs: {sorted(xids_found & unconfirmed_xids)}"
        )
    else:
        return AutoLabel(result="no_hw_issue")


def logs_analysis_heuristic(key_findings: str, tool_results: List[Dict[str, Any]]) -> AutoLabel:
    """
    Determine log analysis outcome.

    Check for software config errors, numerical instability, or no issues.
    """
    findings_lower = key_findings.lower()

    # Check for software config errors
    if "unsupported qat_params" in findings_lower:
        return AutoLabel(result="software_config_error", evidence="Unsupported QAT_PARAMS detected")

    # Check for numerical instability
    numerical_patterns = [r"\binf\b", r"\bnan\b", r"\boverflow\b", r"\bunderflow\b"]
    for pattern in numerical_patterns:
        if re.search(pattern, findings_lower):
            return AutoLabel(
                result="numerical_instability", evidence=f"Pattern '{pattern}' detected"
            )

    # Check for specific error patterns
    if "runtimeerror" in findings_lower and "inf" in findings_lower:
        return AutoLabel(result="numerical_instability", evidence="RuntimeError with inf detected")

    return AutoLabel(result="no_issue")


def health_checks_heuristic(key_findings: str, tool_results: List[Dict[str, Any]]) -> AutoLabel:
    """
    Determine health check status.

    Check if all systems are healthy or if failures are present.
    """
    findings_lower = key_findings.lower()

    # Check for failure indicators
    failure_indicators = ["failure", "failed", "error", "unhealthy", "down", "offline"]
    for indicator in failure_indicators:
        if indicator in findings_lower:
            return AutoLabel(
                result="failures_present", evidence=f"'{indicator}' detected in findings"
            )

    # Check for healthy indicators
    if "all healthy" in findings_lower or "no issues" in findings_lower:
        return AutoLabel(result="all_healthy")

    # Default to healthy if no clear failures
    return AutoLabel(result="all_healthy")


def scheduler_analysis_heuristic(
    key_findings: str, tool_results: List[Dict[str, Any]]
) -> AutoLabel:
    """
    Determine scheduler status.

    Check if job was killed by scheduler, clean exit, or unknown.
    """
    findings_lower = key_findings.lower()

    # Check for scheduler-killed indicators
    if any(term in findings_lower for term in ["killed", "terminated", "cancelled", "timeout"]):
        return AutoLabel(result="scheduler_killed", evidence="Job termination detected")

    # Check for clean exit
    if any(term in findings_lower for term in ["completed", "success", "clean"]):
        return AutoLabel(result="scheduler_clean", evidence="Clean completion detected")

    # Check for requeue
    if "requeued" in findings_lower:
        return AutoLabel(result="scheduler_killed", evidence="Job was requeued")

    return AutoLabel(result="unknown")


def network_analysis_heuristic(key_findings: str, tool_results: List[Dict[str, Any]]) -> AutoLabel:
    """
    Determine network status.

    Check for InfiniBand or other network issues.
    """
    findings_lower = key_findings.lower()

    # Check for IB/network issues
    network_issue_patterns = [
        "ib_issue",
        "infiniband",
        "network error",
        "connection failed",
        "nvlink",
        "nvswitch",
        "communication failure",
        "nccl",
    ]

    for pattern in network_issue_patterns:
        if pattern in findings_lower:
            return AutoLabel(result="ib_issue", evidence=f"'{pattern}' detected")

    # Check for SXID errors (often network-related)
    if "sxid" in findings_lower:
        return AutoLabel(result="ib_issue", evidence="SXID error indicates network issue")

    return AutoLabel(result="no_ib_issue")


def storage_analysis_heuristic(key_findings: str, tool_results: List[Dict[str, Any]]) -> AutoLabel:
    """
    Determine storage status.

    Check for metadata spikes or normal I/O patterns.
    """
    findings_lower = key_findings.lower()

    # Check for metadata spike indicators
    if "metadata" in findings_lower:
        if any(term in findings_lower for term in ["spike", "massive", "surge", "10x", "100x"]):
            # Determine if primary or secondary
            if "primary" in findings_lower:
                return AutoLabel(
                    result="metadata_spike_primary", evidence="Primary metadata spike detected"
                )
            else:
                return AutoLabel(
                    result="metadata_spike_secondary", evidence="Secondary metadata spike detected"
                )

    # Check for storage issues
    if any(term in findings_lower for term in ["storage failure", "i/o error", "disk error"]):
        return AutoLabel(result="metadata_spike_secondary", evidence="Storage error detected")

    return AutoLabel(result="normal_io")


def job_info_heuristic(key_findings: str, tool_results: List[Dict[str, Any]]) -> AutoLabel:
    """
    Determine job status.

    Extract job success/failure status and reason.
    """
    findings_lower = key_findings.lower()

    # Check job status
    if "requeued" in findings_lower:
        # Extract reason if possible
        reason_match = re.search(r"(runtimeerror|error|failure|crash)", findings_lower)
        reason = reason_match.group(1) if reason_match else "unknown"
        return AutoLabel(result="failed", evidence=f"Job requeued due to {reason}")

    if any(term in findings_lower for term in ["failed", "failure", "error", "crash"]):
        return AutoLabel(result="failed", evidence="Job failure detected")

    if any(term in findings_lower for term in ["success", "completed", "finished"]):
        return AutoLabel(result="succeeded", evidence="Job completed successfully")

    # Default based on common patterns
    return AutoLabel(result="failed", evidence="Default assumption based on context")


def final_analysis_heuristic(key_findings: str, tool_results: List[Dict[str, Any]]) -> AutoLabel:
    """
    Extract root cause and confidence from final analysis.

    This is more complex as it needs to extract both root_cause and confidence.
    """
    findings_lower = key_findings.lower()

    # Try to extract root cause
    root_cause = "unknown"
    confidence = 0.5  # Default confidence

    # Hardware-related root causes
    if any(term in findings_lower for term in ["hardware", "xid", "sxid", "gpu failure"]):
        root_cause = "hardware_failure"
        confidence = 0.9 if "confirmed" in findings_lower else 0.7

    # Numerical instability
    elif any(term in findings_lower for term in ["inf", "nan", "numerical", "gradient"]):
        root_cause = "numerical_instability"
        confidence = 0.85

    # Software configuration
    elif any(term in findings_lower for term in ["config", "qat_params", "software"]):
        root_cause = "software_config_error"
        confidence = 0.8

    # Network issues
    elif any(term in findings_lower for term in ["network", "nvlink", "nvswitch", "communication"]):
        root_cause = "network_failure"
        confidence = 0.75

    # Storage issues
    elif any(term in findings_lower for term in ["storage", "metadata", "i/o"]):
        root_cause = "storage_issue"
        confidence = 0.7

    # Try to extract confidence if explicitly mentioned
    confidence_match = re.search(r"confidence[:\s]+(\d+(?:\.\d+)?)", findings_lower)
    if confidence_match:
        try:
            extracted_conf = float(confidence_match.group(1))
            # Handle percentage vs decimal
            if extracted_conf > 1:
                extracted_conf = extracted_conf / 100
            confidence = extracted_conf
        except ValueError:
            pass

    # High confidence keywords
    if any(
        term in findings_lower for term in ["high confidence", "confirmed", "clear", "definitive"]
    ):
        confidence = max(confidence, 0.9)
    elif any(term in findings_lower for term in ["low confidence", "uncertain", "unclear"]):
        confidence = min(confidence, 0.4)

    return AutoLabel(result=root_cause, evidence=f"confidence={confidence}")


def apply_heuristic(
    task_name: str, key_findings: str, tool_results: List[Dict[str, Any]]
) -> AutoLabel:
    """
    Apply the appropriate heuristic based on task name.

    Args:
        task_name: Name of the task
        key_findings: Key findings text
        tool_results: Tool results from debug trace

    Returns:
        AutoLabel with heuristic result
    """
    heuristic_map = {
        "gpu_hw_analysis": gpu_hw_analysis_heuristic,
        "logs_analysis": logs_analysis_heuristic,
        "health_checks": health_checks_heuristic,
        "scheduler_analysis": scheduler_analysis_heuristic,
        "network_analysis": network_analysis_heuristic,
        "storage_analysis": storage_analysis_heuristic,
        "job_info": job_info_heuristic,
        "final_analysis": final_analysis_heuristic,
    }

    heuristic_func = heuristic_map.get(task_name)
    if not heuristic_func:
        # Unknown task, return generic label
        return AutoLabel(result="unknown", evidence="No heuristic for this task")

    return heuristic_func(key_findings, tool_results)
