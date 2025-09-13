"""
IDOL - Incremental DAG Optimization for Learning

A system for transforming debug traces into validated golden datasets.
"""

__version__ = "0.1.0"

from idol.freezer import freeze_task
from idol.harvester import generate_candidates, parse_debug_trace
from idol.reviewer import review_task

__all__ = [
    "generate_candidates",
    "parse_debug_trace",
    "review_task",
    "freeze_task",
    "__version__",
]
