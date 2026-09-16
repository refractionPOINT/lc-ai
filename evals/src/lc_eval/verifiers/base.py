"""Small, model-independent verifier primitives.

Verifiers consume only already-frozen dictionaries.  They deliberately do not
perform SDK, HTTP, or filesystem reads, so regrading cannot change the evidence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal

Status = Literal["pass", "fail", "unknown"]


def assertion(
    assertion_id: str,
    status: Status,
    *,
    required: bool = True,
    expected: Any = None,
    observed: Any = None,
    evidence: Sequence[str] = (),
    explanation: str,
) -> dict[str, Any]:
    """Return the stable, JSON-safe assertion contract used by every grader."""

    if status not in {"pass", "fail", "unknown"}:
        raise ValueError(f"invalid assertion status: {status!r}")
    return {
        "id": assertion_id,
        "status": status,
        "required": bool(required),
        "expected": expected,
        "observed": observed,
        "evidence": list(evidence),
        "explanation": explanation,
    }


def evidence_refs(value: Any, fallback: str) -> list[str]:
    """Extract evidence references without accidentally treating text as a list."""

    if isinstance(value, Mapping):
        refs = value.get("evidence_refs")
        if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)):
            return [str(item) for item in refs]
    return [fallback]


def merge_evidence(*values: Mapping[str, Any] | None) -> dict[str, Any]:
    """Merge evidence sources left-to-right and copy only their top level."""

    merged: dict[str, Any] = {}
    for value in values:
        if isinstance(value, Mapping):
            merged.update(value)
    return merged


def summarize_ids(values: set[str], *, limit: int = 20) -> dict[str, Any]:
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "ids": ordered[:limit],
        "truncated": len(ordered) > limit,
    }


def grade(assertions: Sequence[Mapping[str, Any]]) -> str:
    """Calculate a trial grade from required assertions."""

    required = [item for item in assertions if item.get("required", True)]
    if not required:
        return "inconclusive"
    if any(item.get("status") == "fail" for item in required):
        return "fail"
    if any(item.get("status") != "pass" for item in required):
        return "inconclusive"
    return "pass"
