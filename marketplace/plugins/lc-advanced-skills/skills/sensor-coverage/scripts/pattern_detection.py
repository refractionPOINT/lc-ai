#!/usr/bin/env python3
"""
Pattern Detection Algorithms for Fleet Analysis

These functions are used by the fleet-pattern-analyzer agent to detect
systemic issues across multiple LimaCharlie organizations.

Usage: Reference these functions when implementing pattern detection logic.
The agent should follow the algorithm structure when analyzing fleet data.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import os


def detect_platform_degradation(org_results: List[Dict], threshold_pct: float = 10) -> List[Dict]:
    """
    Flag platforms where fleet-wide offline rate exceeds threshold.

    Args:
        org_results: List of per-org coverage results from org-coverage-reporter
        threshold_pct: Percentage offline rate to trigger alert (default: 10%)

    Returns:
        List of degraded platform records with affected orgs
    """
    platform_totals = {}

    for org in org_results:
        if org.get('status') == 'failed':
            continue
        for platform, stats in org.get('platforms', {}).items():
            if platform not in platform_totals:
                platform_totals[platform] = {'total': 0, 'offline': 0, 'orgs': []}
            platform_totals[platform]['total'] += stats['total']
            platform_totals[platform]['offline'] += stats['offline']
            if stats['offline'] > 0:
                platform_totals[platform]['orgs'].append({
                    'org_name': org['org_name'],
                    'total': stats['total'],
                    'offline': stats['offline'],
                    'offline_pct': stats.get('offline_pct', 0)
                })

    degraded_platforms = []
    for platform, totals in platform_totals.items():
        if totals['total'] == 0:
            continue
        offline_pct = (totals['offline'] / totals['total']) * 100
        if offline_pct > threshold_pct:
            degraded_platforms.append({
                'platform': platform,
                'total_sensors': totals['total'],
                'offline_sensors': totals['offline'],
                'offline_pct': offline_pct,
                'threshold_pct': threshold_pct,
                'affected_orgs': sorted(totals['orgs'],
                                       key=lambda x: x['offline_pct'],
                                       reverse=True),
                'org_count': len(totals['orgs'])
            })

    return degraded_platforms


def find_hostname_pattern(hostnames: List[str]) -> Optional[str]:
    """Find common prefix/suffix patterns in hostnames."""
    if not hostnames:
        return None

    # Check for common prefix
    prefix = os.path.commonprefix(hostnames)
    if len(prefix) >= 3:
        return f"{prefix}*"

    # Check for common patterns like test-*, vm-*, etc.
    patterns = ['test-', 'vm-', 'dev-', 'temp-', 'new-']
    for pattern in patterns:
        if sum(1 for h in hostnames if h.lower().startswith(pattern)) > len(hostnames) / 2:
            return f"{pattern}*"

    return None


def parse_timestamp(ts_str: str) -> float:
    """Parse timestamp string to Unix epoch."""
    try:
        dt = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%SZ')
        return dt.timestamp()
    except ValueError:
        try:
            dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
            return dt.timestamp()
        except ValueError:
            return 0


def detect_coordinated_enrollment(org_results: List[Dict],
                                   min_sensors: int = 5,
                                   window_hours: int = 2) -> List[Dict]:
    """
    Detect clusters of new sensor enrollments across orgs within time window.

    Args:
        org_results: List of per-org coverage results
        min_sensors: Minimum sensors to form a cluster (default: 5)
        window_hours: Time window for clustering (default: 2 hours)

    Returns:
        List of enrollment cluster records
    """
    all_new_sensors = []
    for org in org_results:
        if org.get('status') == 'failed':
            continue
        for sensor in org.get('new_sensors_24h', []):
            all_new_sensors.append({
                'org_name': org['org_name'],
                'oid': org['oid'],
                'sid': sensor['sid'],
                'hostname': sensor['hostname'],
                'enrolled_at': parse_timestamp(sensor.get('enrolled_at', '')),
                'platform': sensor.get('platform', 'unknown'),
                'tags': sensor.get('tags', [])
            })

    if len(all_new_sensors) < min_sensors:
        return []

    # Sort by enrollment time
    all_new_sensors.sort(key=lambda x: x['enrolled_at'])

    # Detect time clusters using sliding window
    window_seconds = window_hours * 3600
    clusters = []

    i = 0
    while i < len(all_new_sensors):
        cluster = [all_new_sensors[i]]
        j = i + 1
        while j < len(all_new_sensors):
            if all_new_sensors[j]['enrolled_at'] - cluster[0]['enrolled_at'] <= window_seconds:
                cluster.append(all_new_sensors[j])
                j += 1
            else:
                break

        # Check if cluster spans multiple orgs and meets minimum size
        unique_orgs = set(s['org_name'] for s in cluster)
        if len(cluster) >= min_sensors and len(unique_orgs) > 1:
            hostnames = [s['hostname'] for s in cluster]
            common_pattern = find_hostname_pattern(hostnames)

            clusters.append({
                'sensors': cluster,
                'count': len(cluster),
                'org_count': len(unique_orgs),
                'orgs': list(unique_orgs),
                'start_time': cluster[0]['enrolled_at'],
                'end_time': cluster[-1]['enrolled_at'],
                'hostname_pattern': common_pattern,
                'window_hours': window_hours
            })

        i = j if j > i + 1 else i + 1

    return clusters


def analyze_sla_compliance(org_results: List[Dict],
                           alert_threshold_pct: float = 20) -> Dict:
    """
    Analyze SLA compliance patterns and identify systemic issues.

    Args:
        org_results: List of per-org coverage results
        alert_threshold_pct: Trigger alert if this % of orgs fail SLA

    Returns:
        SLA compliance analysis with patterns
    """
    successful_orgs = [o for o in org_results if o.get('status') != 'failed']

    passing = [o for o in successful_orgs
               if o.get('coverage', {}).get('sla_status') == 'PASSING']
    failing = [o for o in successful_orgs
               if o.get('coverage', {}).get('sla_status') == 'FAILING']

    failure_rate = (len(failing) / len(successful_orgs) * 100) if successful_orgs else 0

    patterns = []

    # Check if failure rate exceeds threshold
    if failure_rate >= alert_threshold_pct:
        patterns.append({
            'pattern_type': 'high_failure_rate',
            'description': f'{failure_rate:.1f}% of organizations failing SLA',
            'threshold': alert_threshold_pct,
            'failing_count': len(failing),
            'total_count': len(successful_orgs)
        })

    return {
        'total_orgs': len(successful_orgs),
        'passing': len(passing),
        'failing': len(failing),
        'failure_rate_pct': failure_rate,
        'alert_triggered': failure_rate >= alert_threshold_pct,
        'failing_orgs': sorted(failing,
                               key=lambda x: x.get('coverage', {}).get('coverage_pct', 0)),
        'patterns': patterns
    }


def analyze_risk_concentration(org_results: List[Dict]) -> Dict:
    """
    Check if critical/high risk sensors are concentrated or distributed.

    Args:
        org_results: List of per-org coverage results

    Returns:
        Risk concentration analysis
    """
    successful_orgs = [o for o in org_results if o.get('status') != 'failed']

    total_critical = sum(o.get('risk_distribution', {}).get('critical', 0)
                        for o in successful_orgs)
    total_high = sum(o.get('risk_distribution', {}).get('high', 0)
                    for o in successful_orgs)

    orgs_with_critical = [
        {
            'org_name': o['org_name'],
            'critical_count': o.get('risk_distribution', {}).get('critical', 0),
            'high_count': o.get('risk_distribution', {}).get('high', 0),
            'total_sensors': o.get('coverage', {}).get('total_sensors', 0)
        }
        for o in successful_orgs
        if o.get('risk_distribution', {}).get('critical', 0) > 0
    ]

    is_concentrated = False
    concentration_detail = None

    if total_critical > 0 and len(orgs_with_critical) <= 3:
        is_concentrated = True
        concentration_detail = {
            'type': 'concentrated',
            'description': f'{total_critical} critical-risk sensors in only {len(orgs_with_critical)} organizations',
            'orgs': orgs_with_critical
        }

    return {
        'total_critical': total_critical,
        'total_high': total_high,
        'orgs_with_critical': len(orgs_with_critical),
        'is_concentrated': is_concentrated,
        'concentration_detail': concentration_detail,
        'critical_orgs': sorted(orgs_with_critical,
                                key=lambda x: x['critical_count'],
                                reverse=True)
    }


def detect_temporal_correlation(org_results: List[Dict]) -> Dict:
    """
    Check if sensors across orgs went offline at similar times.

    Args:
        org_results: List of per-org coverage results

    Returns:
        Temporal correlation analysis
    """
    successful_orgs = [o for o in org_results if o.get('status') != 'failed']

    total_sensors = sum(o.get('coverage', {}).get('total_sensors', 0)
                       for o in successful_orgs)
    total_offline = sum(o.get('coverage', {}).get('offline', 0)
                       for o in successful_orgs)
    avg_offline_rate = (total_offline / total_sensors * 100) if total_sensors > 0 else 0

    # Find orgs with significantly higher offline rates
    spike_threshold = avg_offline_rate * 2  # 2x average = spike
    orgs_with_spikes = []

    for o in successful_orgs:
        coverage = o.get('coverage', {})
        if coverage.get('offline', 0) > 0:
            total = coverage.get('total_sensors', 0)
            if total > 0:
                offline_rate = (coverage['offline'] / total * 100)
                if offline_rate > spike_threshold:
                    orgs_with_spikes.append(o)

    if len(orgs_with_spikes) >= 3:
        return {
            'pattern_detected': True,
            'description': f'{len(orgs_with_spikes)} organizations showing offline spikes (>{spike_threshold:.1f}%)',
            'avg_offline_rate': avg_offline_rate,
            'spike_threshold': spike_threshold,
            'affected_orgs': [
                {
                    'org_name': o['org_name'],
                    'offline_rate': o['coverage']['offline'] / o['coverage']['total_sensors'] * 100,
                    'offline_count': o['coverage']['offline']
                }
                for o in orgs_with_spikes
            ]
        }

    return {'pattern_detected': False}


if __name__ == '__main__':
    # Example usage / test
    print("Pattern Detection Algorithms for sensor-coverage skill")
    print("Import and use these functions for fleet analysis")
