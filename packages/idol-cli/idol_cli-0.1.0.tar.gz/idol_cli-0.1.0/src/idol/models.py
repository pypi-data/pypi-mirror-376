"""
Pydantic models for IDOL system data structures.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ToolCall(BaseModel):
    """Represents a tool call in the debug trace."""

    name: str
    args: Dict[str, Any] = {}


class TaskInput(BaseModel):
    """Input data for a task execution."""

    job_id: int
    attempt: int
    key_findings: str
    tool_calls: List[ToolCall]


class AutoLabel(BaseModel):
    """Auto-generated label from heuristics."""

    result: str
    evidence: Optional[str] = None


class GoldLabel(BaseModel):
    """Gold standard label (can be auto or human-validated)."""

    result: Optional[str] = None
    root_cause: Optional[str] = None  # For final_analysis task
    confidence: Optional[float] = None  # For final_analysis task
    evidence: Optional[str] = None

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        """Ensure confidence is between 0 and 1."""
        if v is not None and not 0 <= v <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return v


class CandidateRecord(BaseModel):
    """A candidate record for review."""

    id: str  # SHA1 hash
    task: str
    input: TaskInput
    auto: AutoLabel
    status: Literal["pending", "accepted", "reviewed"] = "pending"


class OverrideRecord(BaseModel):
    """Human override for a candidate."""

    id: str
    gold: GoldLabel
    note: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FrozenRecord(BaseModel):
    """Final frozen record for training."""

    id: str
    input: TaskInput
    gold: GoldLabel
