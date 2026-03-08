#!/usr/bin/env python3
"""
Sensor Classification and Risk Scoring Algorithms

These functions are used by the org-coverage-reporter agent to classify
sensors and calculate risk scores within a single organization.

Usage: Reference these functions when implementing sensor classification logic.
"""

from datetime import datetime
from typing import Dict, List, Any, Set, Tuple


# Platform code mappings
# Source of truth: CONSTANTS.md (from go-limacharlie/limacharlie/identification.go)
PLATFORM_CODES = {
    # EDR platforms
    268435456: 'windows',       # 0x10000000
    536870912: 'linux',         # 0x20000000
    805306368: 'macos',         # 0x30000000
    1073741824: 'ios',          # 0x40000000
    1342177280: 'android',      # 0x50000000
    1610612736: 'chromeos',     # 0x60000000
    1879048192: 'vpn',          # 0x70000000
    # USP adapter platforms
    2147483648: 'adapter-text',      # 0x80000000
    2415919104: 'adapter-json',      # 0x90000000
    2684354560: 'cloud-gcp',         # 0xA0000000
    2952790016: 'cloud-aws',         # 0xB0000000
    3221225472: 'cloud-carbonblack', # 0xC0000000
    3489660928: 'cloud-1password',   # 0xD0000000
    3758096384: 'cloud-o365',        # 0xE0000000
    4026531840: 'cloud-sophos',      # 0xF0000000
    16777216: 'cloud-crowdstrike',   # 0x01000000
    67108864: 'cloud-msdefender',    # 0x04000000
    83886080: 'cloud-duo',           # 0x05000000
    100663296: 'cloud-okta',         # 0x06000000
    117440512: 'cloud-sentinelone',  # 0x07000000
    134217728: 'cloud-github',       # 0x08000000
    150994944: 'cloud-slack',        # 0x09000000
    201326592: 'cloud-azuread',      # 0x0C000000
    218103808: 'cloud-azuremonitor', # 0x0D000000
}

# System tag prefixes to ignore when checking for user tags
SYSTEM_TAG_PREFIXES = ['lc:', 'chrome:']


def parse_alive_timestamp(alive_str: str) -> float:
    """
    Parse the alive field format to Unix timestamp.

    Args:
        alive_str: Timestamp string like "2025-12-05 14:22:13"

    Returns:
        Unix timestamp (float)
    """
    try:
        alive_dt = datetime.strptime(alive_str, '%Y-%m-%d %H:%M:%S')
        return alive_dt.timestamp()
    except (ValueError, TypeError):
        return 0


def classify_offline_duration(hours_offline: float) -> str:
    """
    Classify sensor by how long it's been offline.

    Args:
        hours_offline: Hours since last seen

    Returns:
        Category string: online, recent_24h, short_1_7d, medium_7_30d, critical_30d_plus
    """
    if hours_offline < 0:
        return "online"
    elif hours_offline < 24:
        return "recent_24h"
    elif hours_offline < 168:  # 7 days
        return "short_1_7d"
    elif hours_offline < 720:  # 30 days
        return "medium_7_30d"
    else:
        return "critical_30d_plus"


def get_platform_name(platform_code: int) -> str:
    """
    Convert platform code to human-readable name.

    Args:
        platform_code: Numeric platform identifier

    Returns:
        Platform name string
    """
    return PLATFORM_CODES.get(platform_code, f'unknown-{platform_code}')


def is_edr_platform(platform_code: int, architecture: int = None) -> bool:
    """
    Check if sensor is an EDR endpoint (vs adapter/extension/cloud).

    An EDR sensor must have:
    - Platform that is NOT in the non-EDR platforms list
    - Architecture that is NOT 9 (usp_adapter)

    A sensor on Linux/Windows/macOS platform but with architecture 9 is an
    adapter (USP), not an EDR agent, and cannot be tasked.

    Args:
        platform_code: Numeric platform identifier
        architecture: Numeric architecture identifier (optional). If 9 (usp_adapter),
                     the sensor is NOT an EDR regardless of platform.

    Returns:
        True if EDR endpoint that can be tasked
    """
    # Architecture 9 = usp_adapter (USP adapter), never an EDR
    if architecture == 9:
        return False

    # Non-EDR platforms (USP adapters, cloud integrations)
    # These cannot be tasked with EDR commands
    non_edr_platforms = {
        2147483648,   # adapter-text (0x80000000)
        2415919104,   # adapter-json (0x90000000)
        2684354560,   # cloud-gcp (0xA0000000)
        2952790016,   # cloud-aws (0xB0000000)
        3221225472,   # cloud-carbonblack (0xC0000000)
        3489660928,   # cloud-1password (0xD0000000)
        3758096384,   # cloud-o365 (0xE0000000)
        4026531840,   # cloud-sophos (0xF0000000)
        16777216,     # cloud-crowdstrike (0x01000000)
        67108864,     # cloud-msdefender (0x04000000)
        83886080,     # cloud-duo (0x05000000)
        100663296,    # cloud-okta (0x06000000)
        117440512,    # cloud-sentinelone (0x07000000)
        134217728,    # cloud-github (0x08000000)
        150994944,    # cloud-slack (0x09000000)
        201326592,    # cloud-azuread (0x0C000000)
        218103808,    # cloud-azuremonitor (0x0D000000)
    }
    return platform_code not in non_edr_platforms


def get_user_tags(tags: List[str]) -> List[str]:
    """
    Filter out system tags, returning only user-defined tags.

    Args:
        tags: List of all tags on sensor

    Returns:
        List of user-defined tags only
    """
    return [t for t in (tags or [])
            if not any(t.startswith(p) for p in SYSTEM_TAG_PREFIXES)]


def is_new_sensor(enroll_timestamp: float, now_timestamp: float,
                   window_hours: int = 24) -> bool:
    """
    Check if sensor was enrolled within the detection window.

    Args:
        enroll_timestamp: Unix timestamp of enrollment
        now_timestamp: Current Unix timestamp
        window_hours: Hours to consider as "new" (default: 24)

    Returns:
        True if sensor is new
    """
    window_seconds = window_hours * 3600
    return (now_timestamp - enroll_timestamp) < window_seconds


def calculate_risk_score(sensor: Dict, now_timestamp: float) -> Tuple[int, List[str]]:
    """
    Calculate risk score for a sensor based on multiple factors.

    Risk Scoring Formula (0-100):
    - Offline 30+ days: +40
    - Offline 7-30 days: +25
    - Offline 1-7 days: +15
    - Offline < 24h: +5
    - Online but silent 24h+: +30
    - Online but degraded: +15
    - Untagged sensor: +10
    - New asset 24h: +15
    - Missing expected asset: +35

    Args:
        sensor: Sensor data dict with classification info
        now_timestamp: Current Unix timestamp

    Returns:
        Tuple of (risk_score, list_of_risk_factors)
    """
    score = 0
    factors = []

    category = sensor.get('offline_category', 'online')

    # Offline duration scoring
    if category == 'critical_30d_plus':
        score += 40
        factors.append('offline_30d_plus')
    elif category == 'medium_7_30d':
        score += 25
        factors.append('offline_7_30d')
    elif category == 'short_1_7d':
        score += 15
        factors.append('offline_1_7d')
    elif category == 'recent_24h':
        score += 5
        factors.append('offline_recent')

    # Telemetry health scoring (for online sensors)
    telemetry_status = sensor.get('telemetry_status')
    if telemetry_status == 'silent':
        score += 30
        factors.append('online_silent')
    elif telemetry_status == 'degraded':
        score += 15
        factors.append('online_degraded')

    # Untagged scoring
    if sensor.get('is_untagged', False):
        score += 10
        factors.append('untagged')

    # New sensor scoring (Shadow IT risk)
    if sensor.get('is_new_24h', False) and sensor.get('is_untagged', False):
        score += 15
        factors.append('new_untagged')

    return min(score, 100), factors


def get_severity_level(risk_score: int) -> str:
    """
    Convert risk score to severity level.

    Args:
        risk_score: Numeric risk score (0-100)

    Returns:
        Severity string: critical, high, medium, low
    """
    if risk_score >= 60:
        return 'critical'
    elif risk_score >= 40:
        return 'high'
    elif risk_score >= 20:
        return 'medium'
    else:
        return 'low'


def classify_sensor(sensor: Dict,
                    online_sids: Set[str],
                    now_timestamp: float) -> Dict:
    """
    Fully classify a sensor with all relevant metadata.

    Args:
        sensor: Raw sensor data from API
        online_sids: Set of currently online sensor IDs
        now_timestamp: Current Unix timestamp

    Returns:
        Enriched sensor dict with classification data
    """
    sid = sensor.get('sid', '')
    is_online = sid in online_sids

    # Parse timestamps
    alive_ts = parse_alive_timestamp(sensor.get('alive', ''))
    enroll_ts = parse_alive_timestamp(sensor.get('enroll', ''))

    # Calculate offline duration
    if is_online:
        hours_offline = -1
        offline_category = 'online'
    else:
        hours_offline = (now_timestamp - alive_ts) / 3600 if alive_ts > 0 else 9999
        offline_category = classify_offline_duration(hours_offline)

    # Get platform and architecture info
    platform_code = sensor.get('plat', sensor.get('platform', 0))
    architecture = sensor.get('arch', sensor.get('architecture'))
    platform_name = get_platform_name(platform_code)
    # Check both platform AND architecture - arch=9 (usp_adapter) means NOT an EDR
    is_edr = is_edr_platform(platform_code, architecture)

    # Get user tags
    user_tags = get_user_tags(sensor.get('tags', []))
    is_untagged = len(user_tags) == 0

    # Check if new
    is_new = is_new_sensor(enroll_ts, now_timestamp) if enroll_ts > 0 else False

    # Build enriched sensor record
    enriched = {
        'sid': sid,
        'hostname': sensor.get('hostname', ''),
        'is_online': is_online,
        'hours_offline': hours_offline if not is_online else 0,
        'offline_category': offline_category,
        'platform_code': platform_code,
        'architecture': architecture,
        'platform_name': platform_name,
        'is_edr': is_edr,
        'tags': sensor.get('tags', []),
        'user_tags': user_tags,
        'is_untagged': is_untagged,
        'is_new_24h': is_new,
        'alive_timestamp': alive_ts,
        'enroll_timestamp': enroll_ts,
        'internal_ip': sensor.get('int_ip', sensor.get('internal_ip', '')),
        'external_ip': sensor.get('ext_ip', sensor.get('external_ip', ''))
    }

    # Calculate risk score
    risk_score, risk_factors = calculate_risk_score(enriched, now_timestamp)
    enriched['risk_score'] = risk_score
    enriched['risk_factors'] = risk_factors
    enriched['severity'] = get_severity_level(risk_score)

    return enriched


def aggregate_statistics(classified_sensors: List[Dict],
                         sla_target: float = 95) -> Dict:
    """
    Aggregate statistics from classified sensors.

    Args:
        classified_sensors: List of enriched sensor dicts
        sla_target: Coverage percentage target

    Returns:
        Aggregated statistics dict
    """
    total = len(classified_sensors)
    if total == 0:
        return {
            'coverage': {'total_sensors': 0, 'online': 0, 'offline': 0,
                        'coverage_pct': 0, 'sla_status': 'N/A'},
            'offline_breakdown': {},
            'risk_distribution': {},
            'platforms': {},
            'tags': {}
        }

    online = [s for s in classified_sensors if s['is_online']]
    offline = [s for s in classified_sensors if not s['is_online']]

    coverage_pct = (len(online) / total * 100)
    sla_status = 'PASSING' if coverage_pct >= sla_target else 'FAILING'

    # Offline breakdown
    offline_breakdown = {
        'recent_24h': len([s for s in classified_sensors if s['offline_category'] == 'recent_24h']),
        'short_1_7d': len([s for s in classified_sensors if s['offline_category'] == 'short_1_7d']),
        'medium_7_30d': len([s for s in classified_sensors if s['offline_category'] == 'medium_7_30d']),
        'critical_30d_plus': len([s for s in classified_sensors if s['offline_category'] == 'critical_30d_plus'])
    }

    # Risk distribution
    risk_distribution = {
        'critical': len([s for s in classified_sensors if s['severity'] == 'critical']),
        'high': len([s for s in classified_sensors if s['severity'] == 'high']),
        'medium': len([s for s in classified_sensors if s['severity'] == 'medium']),
        'low': len([s for s in classified_sensors if s['severity'] == 'low'])
    }

    # Platform breakdown
    platforms = {}
    for sensor in classified_sensors:
        plat = sensor['platform_name']
        if plat not in platforms:
            platforms[plat] = {'total': 0, 'online': 0, 'offline': 0}
        platforms[plat]['total'] += 1
        if sensor['is_online']:
            platforms[plat]['online'] += 1
        else:
            platforms[plat]['offline'] += 1

    for plat in platforms:
        platforms[plat]['offline_pct'] = (
            platforms[plat]['offline'] / platforms[plat]['total'] * 100
        ) if platforms[plat]['total'] > 0 else 0

    # Tag breakdown (user tags only)
    tags = {}
    for sensor in classified_sensors:
        for tag in sensor.get('user_tags', []):
            if tag not in tags:
                tags[tag] = {'total': 0, 'online': 0, 'offline': 0}
            tags[tag]['total'] += 1
            if sensor['is_online']:
                tags[tag]['online'] += 1
            else:
                tags[tag]['offline'] += 1

    return {
        'coverage': {
            'total_sensors': total,
            'online': len(online),
            'offline': len(offline),
            'coverage_pct': coverage_pct,
            'sla_target': sla_target,
            'sla_status': sla_status
        },
        'offline_breakdown': offline_breakdown,
        'risk_distribution': risk_distribution,
        'platforms': platforms,
        'tags': tags
    }


def generate_top_issues(stats: Dict, classified_sensors: List[Dict]) -> List[str]:
    """
    Generate human-readable issue summaries.

    Args:
        stats: Aggregated statistics dict
        classified_sensors: List of enriched sensor dicts

    Returns:
        List of issue strings, priority ordered
    """
    issues = []
    coverage = stats.get('coverage', {})
    breakdown = stats.get('offline_breakdown', {})

    # SLA failure (highest priority)
    if coverage.get('sla_status') == 'FAILING':
        gap = coverage.get('sla_target', 95) - coverage.get('coverage_pct', 0)
        issues.append(
            f"SLA FAILING: {coverage['coverage_pct']:.1f}% coverage "
            f"(target: {coverage['sla_target']}%, gap: {gap:.1f}%)"
        )

    # Critical offline
    critical = breakdown.get('critical_30d_plus', 0)
    if critical > 0:
        issues.append(f"{critical} sensor(s) offline 30+ days (critical)")

    # Medium offline
    medium = breakdown.get('medium_7_30d', 0)
    if medium > 0:
        issues.append(f"{medium} sensor(s) offline 7-30 days")

    # Short offline
    short = breakdown.get('short_1_7d', 0)
    if short > 0:
        issues.append(f"{short} sensor(s) offline 1-7 days")

    # Untagged
    untagged = len([s for s in classified_sensors if s.get('is_untagged', False)])
    if untagged > 0:
        issues.append(f"{untagged} untagged sensor(s)")

    # New sensors (Shadow IT)
    new_sensors = len([s for s in classified_sensors if s.get('is_new_24h', False)])
    if new_sensors > 0:
        issues.append(f"{new_sensors} new sensor(s) in 24h (Shadow IT risk)")

    # Silent sensors
    silent = len([s for s in classified_sensors
                  if s.get('telemetry_status') == 'silent'])
    if silent > 0:
        issues.append(f"{silent} silent sensor(s) (online but no events)")

    return issues


if __name__ == '__main__':
    print("Sensor Classification Algorithms for sensor-coverage skill")
    print("Import and use these functions for sensor analysis")
