"""Hidden answer-key storage for practice tasks.

Solutions are kept in the _solutions/ folder (one file per task).
The user never needs to open this folder — it's only read by the assistant
to verify the user's work and generate targeted feedback.
"""
from __future__ import annotations

from pathlib import Path

_SOLUTIONS_DIR = Path("_solutions")


def _task_path(task_id: str | int) -> Path:
    _SOLUTIONS_DIR.mkdir(exist_ok=True)
    return _SOLUTIONS_DIR / f"task_{task_id}.py"


def write_solution(task_id: str | int, content: str) -> str:
    """Write the reference solution for *task_id* to the hidden solutions folder."""
    path = _task_path(task_id)
    path.write_text(content, encoding="utf-8")
    return f"Solution for task {task_id} saved to {path}"


def read_solution(task_id: str | int) -> str:
    """Read the reference solution for *task_id* from the hidden solutions folder."""
    path = _task_path(task_id)
    if not path.exists():
        return f"No solution found for task {task_id}."
    return path.read_text(encoding="utf-8")
