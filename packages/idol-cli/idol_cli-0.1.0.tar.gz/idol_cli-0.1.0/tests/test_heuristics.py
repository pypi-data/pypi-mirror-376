"""
Tests for the heuristics module.
"""

from idol.heuristics import (
    apply_heuristic,
    final_analysis_heuristic,
    gpu_hw_analysis_heuristic,
    health_checks_heuristic,
    job_info_heuristic,
    logs_analysis_heuristic,
    network_analysis_heuristic,
    scheduler_analysis_heuristic,
    storage_analysis_heuristic,
)


def test_gpu_hw_analysis_confirmed():
    """Test GPU hardware analysis with confirmed XIDs."""
    # Test confirmed XID
    label = gpu_hw_analysis_heuristic("XID 48 error detected", [])
    assert label.result == "confirmed_hw_failure"
    assert "48" in str(label.evidence)

    # Test multiple confirmed XIDs
    label = gpu_hw_analysis_heuristic("XID 62 and XID 79 errors", [])
    assert label.result == "confirmed_hw_failure"

    # Test SXID (always confirmed)
    label = gpu_hw_analysis_heuristic("SXID-20009 error on node", [])
    assert label.result == "confirmed_hw_failure"
    assert "SXID" in label.evidence


def test_gpu_hw_analysis_unconfirmed():
    """Test GPU hardware analysis with unconfirmed XIDs."""
    label = gpu_hw_analysis_heuristic("XID 31 error detected", [])
    assert label.result == "unconfirmed_xids"
    assert "31" in str(label.evidence)

    label = gpu_hw_analysis_heuristic("XID 94 and XID 137", [])
    assert label.result == "unconfirmed_xids"


def test_gpu_hw_analysis_no_issue():
    """Test GPU hardware analysis with no XIDs."""
    label = gpu_hw_analysis_heuristic("No hardware issues found", [])
    assert label.result == "no_hw_issue"

    label = gpu_hw_analysis_heuristic("Job completed successfully", [])
    assert label.result == "no_hw_issue"


def test_logs_analysis_heuristic():
    """Test logs analysis heuristic."""
    # Software config error
    label = logs_analysis_heuristic("Unsupported QAT_PARAMS detected", [])
    assert label.result == "software_config_error"

    # Numerical instability
    label = logs_analysis_heuristic("RuntimeError: found inf in gradient", [])
    assert label.result == "numerical_instability"

    label = logs_analysis_heuristic("NaN values detected", [])
    assert label.result == "numerical_instability"

    label = logs_analysis_heuristic("Gradient overflow error", [])
    assert label.result == "numerical_instability"

    # No issue
    label = logs_analysis_heuristic("Job running normally", [])
    assert label.result == "no_issue"


def test_health_checks_heuristic():
    """Test health checks heuristic."""
    # Failures present
    label = health_checks_heuristic("Node failure detected", [])
    assert label.result == "failures_present"

    label = health_checks_heuristic("Service is down", [])
    assert label.result == "failures_present"

    # All healthy
    label = health_checks_heuristic("All systems healthy", [])
    assert label.result == "all_healthy"

    label = health_checks_heuristic("No issues found", [])
    assert label.result == "all_healthy"

    # Default to healthy
    label = health_checks_heuristic("Status check complete", [])
    assert label.result == "all_healthy"


def test_scheduler_analysis_heuristic():
    """Test scheduler analysis heuristic."""
    # Scheduler killed
    label = scheduler_analysis_heuristic("Job was killed by scheduler", [])
    assert label.result == "scheduler_killed"

    label = scheduler_analysis_heuristic("Job REQUEUED after timeout", [])
    assert label.result == "scheduler_killed"

    # Clean exit
    label = scheduler_analysis_heuristic("Job completed successfully", [])
    assert label.result == "scheduler_clean"

    # Unknown
    label = scheduler_analysis_heuristic("Job status pending", [])
    assert label.result == "unknown"


def test_network_analysis_heuristic():
    """Test network analysis heuristic."""
    # IB issues
    label = network_analysis_heuristic("InfiniBand error detected", [])
    assert label.result == "ib_issue"

    label = network_analysis_heuristic("NVLink communication failure", [])
    assert label.result == "ib_issue"

    label = network_analysis_heuristic("SXID-20009 error", [])
    assert label.result == "ib_issue"

    # No issues
    label = network_analysis_heuristic("Network performance normal", [])
    assert label.result == "no_ib_issue"


def test_storage_analysis_heuristic():
    """Test storage analysis heuristic."""
    # Metadata spike primary
    label = storage_analysis_heuristic("Primary metadata spike 100x increase", [])
    assert label.result == "metadata_spike_primary"

    # Metadata spike secondary
    label = storage_analysis_heuristic("Metadata surge detected", [])
    assert label.result == "metadata_spike_secondary"

    label = storage_analysis_heuristic("Storage I/O error", [])
    assert label.result == "metadata_spike_secondary"

    # Normal I/O
    label = storage_analysis_heuristic("Storage performance within limits", [])
    assert label.result == "normal_io"


def test_job_info_heuristic():
    """Test job info heuristic."""
    # Failed
    label = job_info_heuristic("Job REQUEUED due to error", [])
    assert label.result == "failed"

    label = job_info_heuristic("Job failed with RuntimeError", [])
    assert label.result == "failed"

    # Succeeded
    label = job_info_heuristic("Job completed successfully", [])
    assert label.result == "succeeded"

    # Default to failed
    label = job_info_heuristic("Job status unknown", [])
    assert label.result == "failed"


def test_final_analysis_heuristic():
    """Test final analysis heuristic."""
    # Hardware failure
    label = final_analysis_heuristic("Confirmed hardware XID failure", [])
    assert label.result == "hardware_failure"
    assert label.evidence
    assert "confidence=" in label.evidence

    # Numerical instability
    label = final_analysis_heuristic("RuntimeError with inf gradient", [])
    assert label.result == "numerical_instability"

    # Extract confidence
    label = final_analysis_heuristic("High confidence: hardware failure", [])
    assert "confidence=" in label.evidence

    # Network failure
    label = final_analysis_heuristic("NVSwitch communication error", [])
    assert label.result == "network_failure"


def test_apply_heuristic():
    """Test applying heuristics by task name."""
    # Known task
    label = apply_heuristic("gpu_hw_analysis", "XID 48 error", [])
    assert label.result == "confirmed_hw_failure"

    # Unknown task
    label = apply_heuristic("unknown_task", "some findings", [])
    assert label.result == "unknown"
    assert "No heuristic" in label.evidence
