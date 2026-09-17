"""Machine-readable and escaped static reporting."""

from .compare import compare_pair, compare_results
from .html import render_html
from .results import acceptance_summary, build_report, command_metrics, dumps_json, write_json

__all__ = [
    "acceptance_summary",
    "build_report",
    "compare_pair",
    "compare_results",
    "command_metrics",
    "dumps_json",
    "render_html",
    "write_json",
]
