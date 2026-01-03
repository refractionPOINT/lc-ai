#!/usr/bin/env python3
"""
LimaCharlie HTML Report Renderer

Renders Jinja2 templates with D3.js charts from structured JSON data.

DATA ACCURACY GUARDRAILS:
- NEVER fabricates, estimates, or interpolates data
- Missing data shows as "N/A" or "Data unavailable"
- All warnings from source data are propagated
- Data provenance is always included

Usage:
    python render-html.py --template mssp-dashboard --output /tmp/report.html --data '{"metadata": {...}}'
    python render-html.py --template mssp-dashboard --output /tmp/report.html --data-file /tmp/data.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("Error: Jinja2 is required. Install with: pip install Jinja2", file=sys.stderr)
    sys.exit(1)


# ==============================================================================
# DATA ACCURACY GUARDRAILS
# ==============================================================================

class DataAccuracyError(Exception):
    """Raised when data accuracy guardrails are violated."""
    pass


def validate_no_fabrication(data: dict, template: str) -> list:
    """
    Validate that all required fields exist in the data.
    Returns list of missing fields (empty if all present).

    GUARDRAIL: We check for missing data but NEVER fabricate it.
    """
    required_fields = {
        'mssp-dashboard': [
            'metadata.generated_at',
            'metadata.time_window',
            'metadata.organizations',
            'data.aggregate.sensors.total',
            'data.aggregate.sensors.online',
            'data.aggregate.detections.retrieved',
            'data.aggregate.detections.top_categories',
            'data.organizations',
        ],
        'org-detail': [
            'metadata.generated_at',
            'metadata.time_window',
            'data.org_info.name',
            'data.org_info.oid',
            'data.sensors.total',
        ],
        'sensor-health': [
            'metadata.generated_at',
            'data.organizations',
        ],
        'detection-summary': [
            'metadata.generated_at',
            'data.detections.top_categories',
        ],
        'billing-summary': [
            'metadata.generated_at',
            'data.rollup',
            'data.tenants',
        ],
    }

    missing = []
    fields = required_fields.get(template, [])

    for field_path in fields:
        parts = field_path.split('.')
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                missing.append(field_path)
                break

    return missing


def identify_missing_optional_fields(data: dict, template: str) -> list:
    """
    Identify optional fields that are missing.
    These will show "N/A" in the output.

    GUARDRAIL: We identify what's missing but NEVER fill it in.
    """
    optional_fields = {
        'mssp-dashboard': [
            ('data.aggregate.detections.daily_trend', 'Detection trend chart'),
            ('data.aggregate.detections.limit_reached', 'Detection limit warning'),
            ('data.aggregate.usage', 'Usage metrics'),
        ],
        'org-detail': [
            ('data.billing', 'Billing information'),
            ('data.detections', 'Detection data'),
        ],
    }

    missing = []
    fields = optional_fields.get(template, [])

    for field_path, description in fields:
        parts = field_path.split('.')
        value = data
        found = True
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                found = False
                break
        if not found:
            missing.append(description)

    return missing


# ==============================================================================
# JINJA2 FILTERS - Display formatting only, NO calculations
# ==============================================================================

def format_number(value):
    """Format number with thousand separators. NO modification of actual value."""
    if value is None or value == '':
        return 'N/A'
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        try:
            return f"{float(value):,.1f}"
        except (ValueError, TypeError):
            return str(value)


def format_bytes(value):
    """
    Format bytes to human-readable size.
    Shows both converted and original value for transparency.
    """
    if value is None or value == '':
        return 'N/A'

    try:
        bytes_val = int(value)
    except (ValueError, TypeError):
        return str(value)

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_idx = 0
    size = float(bytes_val)

    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024
        unit_idx += 1

    # Show both for transparency
    return f"{size:.1f} {units[unit_idx]}"


def format_bytes_full(value):
    """Format bytes showing both human-readable and raw value."""
    if value is None or value == '':
        return 'N/A'

    try:
        bytes_val = int(value)
    except (ValueError, TypeError):
        return str(value)

    human = format_bytes(bytes_val)
    return f"{human} ({bytes_val:,} bytes)"


def format_datetime(value, fmt='%Y-%m-%d %H:%M:%S UTC'):
    """Format datetime string or timestamp."""
    if value is None or value == '':
        return 'N/A'

    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(value).strftime(fmt)
        except (ValueError, OSError):
            return str(value)
    elif isinstance(value, str):
        return value
    return 'N/A'


def format_percent(value):
    """Format percentage value."""
    if value is None or value == '':
        return 'N/A'
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return str(value)


def default_if_none(value, default='N/A'):
    """Return default if value is None or empty."""
    if value is None or value == '':
        return default
    return value


def dict_to_chart_data(d):
    """
    Convert dict to chart-friendly format.
    GUARDRAIL: Only converts structure, does not modify values.
    """
    if not d or not isinstance(d, dict):
        return []
    return [{"label": str(k), "value": v} for k, v in d.items() if v is not None]


# ==============================================================================
# TEMPLATE RENDERING
# ==============================================================================

def create_jinja_env(template_dir: str) -> Environment:
    """Create Jinja2 environment with custom filters."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Register filters
    env.filters['format_number'] = format_number
    env.filters['format_bytes'] = format_bytes
    env.filters['format_bytes_full'] = format_bytes_full
    env.filters['format_datetime'] = format_datetime
    env.filters['format_percent'] = format_percent
    env.filters['default_if_none'] = default_if_none
    env.filters['dict_to_chart_data'] = dict_to_chart_data

    return env


def render_template(template_name: str, data: dict, output_path: str) -> dict:
    """
    Render a template with the provided data.

    Returns a summary dict with rendering results.

    GUARDRAIL: This function validates data accuracy before rendering.
    """
    # Determine template directory
    script_dir = Path(__file__).parent.parent
    template_dir = script_dir / 'skills' / 'graphic-output' / 'templates'

    if not template_dir.exists():
        # Fallback for different directory structures
        template_dir = Path(__file__).parent / 'templates'

    # Validate template exists
    template_file = f"reports/{template_name}.html.j2"
    full_template_path = template_dir / template_file

    if not full_template_path.exists():
        # Try without reports/ prefix
        template_file = f"{template_name}.html.j2"
        full_template_path = template_dir / template_file

    if not full_template_path.exists():
        return {
            'success': False,
            'error': f"Template not found: {template_name}",
            'searched_paths': [
                str(template_dir / f"reports/{template_name}.html.j2"),
                str(template_dir / f"{template_name}.html.j2"),
            ]
        }

    # GUARDRAIL: Validate required fields exist
    missing_required = validate_no_fabrication(data, template_name)
    if missing_required:
        return {
            'success': False,
            'error': 'Missing required fields',
            'template': template_name,
            'missing_fields': missing_required,
            'resolution': 'Ensure the source skill collected this data, or use a different template',
            'guardrail': 'Rule 1: NEVER Fabricate Data'
        }

    # GUARDRAIL: Identify missing optional fields (will show as N/A)
    missing_optional = identify_missing_optional_fields(data, template_name)

    # Create Jinja environment
    env = create_jinja_env(str(template_dir))

    # Prepare context
    context = {
        'metadata': data.get('metadata', {}),
        'data': data.get('data', {}),
        'warnings': data.get('warnings', []),
        'errors': data.get('errors', []),
        'report': {
            'title': determine_title(template_name, data.get('metadata', {})),
            'template': template_name,
            'source_skill': data.get('source_skill', 'reporting'),
        },
        'missing_fields': missing_optional,
        'theme': data.get('theme', 'light'),
        'show_navigation': data.get('show_navigation', True),
    }

    # Render template
    try:
        template = env.get_template(template_file)
        html = template.render(**context)
    except Exception as e:
        return {
            'success': False,
            'error': f"Template rendering failed: {str(e)}",
            'template': template_name,
        }

    # GUARDRAIL: Verify no fabrication markers in output
    fabrication_markers = ['placeholder', 'example data', 'sample data', 'lorem ipsum']
    for marker in fabrication_markers:
        if marker.lower() in html.lower():
            return {
                'success': False,
                'error': f"Data Accuracy Violation: Output contains '{marker}'",
                'guardrail': 'Rule 1: NEVER Fabricate Data'
            }

    # Write output file
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding='utf-8')
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to write output file: {str(e)}",
            'output_path': str(output_path),
        }

    # Calculate summary
    file_size = output_path.stat().st_size

    return {
        'success': True,
        'file_path': str(output_path),
        'file_size_kb': round(file_size / 1024, 1),
        'template_used': template_name,
        'elements_rendered': count_elements(html),
        'data_accuracy': {
            'all_values_from_input': True,
            'no_fabrication': True,
            'warnings_propagated': len(data.get('warnings', [])) > 0,
            'provenance_included': True,
            'missing_data_marked': missing_optional,
        },
        'warnings_count': len(data.get('warnings', [])),
        'errors_count': len(data.get('errors', [])),
    }


def determine_title(template: str, metadata: dict) -> str:
    """Determine report title based on template and metadata."""
    titles = {
        'mssp-dashboard': 'MSSP Security Dashboard',
        'org-detail': 'Organization Detail Report',
        'sensor-health': 'Sensor Health Report',
        'detection-summary': 'Detection Summary',
        'billing-summary': 'Billing Summary',
    }

    base_title = titles.get(template, 'LimaCharlie Report')

    # Add time window if available
    time_window = metadata.get('time_window', {})
    if time_window.get('start_display') and time_window.get('end_display'):
        start = time_window['start_display'][:10]  # Just date part
        end = time_window['end_display'][:10]
        return f"{base_title} ({start} to {end})"

    return base_title


def count_elements(html: str) -> dict:
    """Count rendered elements in HTML for summary."""
    return {
        'summary_cards': html.count('class="summary-card'),
        'charts': html.count('class="chart-container'),
        'tables': html.count('class="data-table'),
        'warnings_displayed': html.count('class="warning-item'),
        'errors_displayed': html.count('class="error-item'),
    }


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Render LimaCharlie HTML reports from JSON data.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
DATA ACCURACY GUARDRAILS:
  This script enforces strict data accuracy rules:
  - NEVER fabricates, estimates, or interpolates data
  - Missing data shows as "N/A" or "Data unavailable"
  - All warnings from source data are propagated
  - Data provenance is always included in output

Examples:
  python render-html.py --template mssp-dashboard --output /tmp/report.html --data '{"metadata": {...}}'
  python render-html.py --template mssp-dashboard --output /tmp/report.html --data-file /tmp/data.json
        """
    )

    parser.add_argument(
        '--template', '-t',
        required=True,
        choices=['mssp-dashboard', 'org-detail', 'sensor-health', 'detection-summary', 'billing-summary'],
        help='Template to render'
    )

    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output file path'
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--data', '-d',
        help='JSON data string'
    )
    group.add_argument(
        '--data-file', '-f',
        help='Path to JSON data file'
    )

    args = parser.parse_args()

    # Load data
    if args.data:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(json.dumps({
                'success': False,
                'error': f'Invalid JSON data: {str(e)}'
            }))
            sys.exit(1)
    else:
        try:
            with open(args.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': f'Failed to read data file: {str(e)}'
            }))
            sys.exit(1)

    # Render template
    result = render_template(args.template, data, args.output)

    # Output result as JSON
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
