"""Dependency-free escaped static HTML rendering."""

from __future__ import annotations

import html
import json
from collections.abc import Mapping, Sequence
from typing import Any


def _text(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, (Mapping, list, tuple)):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    return html.escape(str(value), quote=True)


def _assertions(trial: Mapping[str, Any]) -> str:
    rows = []
    values = trial.get("assertions", [])
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        values = []
    for result in values:
        if not isinstance(result, Mapping):
            continue
        refs = result.get("evidence", [])
        rows.append(
            "<tr>"
            f"<td>{_text(result.get('id'))}</td>"
            f"<td>{_text(result.get('status'))}</td>"
            f"<td>{_text(result.get('expected'))}</td>"
            f"<td>{_text(result.get('observed'))}</td>"
            f"<td>{_text(refs)}</td>"
            f"<td>{_text(result.get('explanation'))}</td>"
            "</tr>"
        )
    return "".join(rows) or '<tr><td colspan="6">No assertions recorded.</td></tr>'


def render_html(report: Mapping[str, Any], *, title: str = "LimaCharlie CLI evaluation") -> str:
    """Render report values only through HTML escaping; no active scripts exist."""

    trial_sections = []
    trials = report.get("trials", [])
    if not isinstance(trials, Sequence) or isinstance(trials, (str, bytes)):
        trials = []
    for trial in trials:
        if not isinstance(trial, Mapping):
            continue
        manifest = trial.get("manifest")
        context = trial.get("context")
        if context is None and isinstance(manifest, Mapping):
            context = manifest.get("context")
        trial_sections.append(
            "<section>"
            f"<h2>Trial {_text(trial.get('trial_id'))}</h2>"
            f"<p>Scenario: {_text(trial.get('scenario_id', trial.get('scenario')))}; "
            f"grade: <strong>{_text(trial.get('grade', trial.get('task_grade')))}</strong>; "
            f"cleanup: {_text(trial.get('cleanup_state', trial.get('cleanup')))}</p>"
            f"<p>Context: {_text(context)}</p>"
            "<table><thead><tr><th>Assertion</th><th>Status</th><th>Expected</th>"
            "<th>Observed</th><th>Evidence</th><th>Explanation</th></tr></thead><tbody>"
            f"{_assertions(trial)}</tbody></table>"
            f"<details><summary>Usage and metrics</summary><pre>{_text({'usage': trial.get('usage'), 'timings': trial.get('timings'), 'metrics': trial.get('metrics')})}</pre></details>"
            "</section>"
        )
    summary = report.get("summary", {})
    acceptance = report.get("acceptance")
    comparisons = report.get("comparisons", [])
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{_text(title)}</title>"
        "<style>body{font:15px system-ui,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1rem}"
        "table{border-collapse:collapse;width:100%}th,td{border:1px solid #bbb;padding:.4rem;text-align:left;vertical-align:top}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere}section{margin:2rem 0}</style></head><body>"
        f"<h1>{_text(title)}</h1><h2>Summary</h2><pre>{_text(summary)}</pre>"
        f"<h2>Acceptance</h2><pre>{_text(acceptance)}</pre>"
        f"<h2>Comparisons</h2><pre>{_text(comparisons)}</pre>"
        f"{''.join(trial_sections)}"
        "</body></html>\n"
    )
