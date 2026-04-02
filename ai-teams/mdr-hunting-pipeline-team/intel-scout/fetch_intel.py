#!/usr/bin/env python3
"""MDR Hunting Pipeline - Threat Intelligence Fetcher

Fetches threat intelligence from multiple public sources and outputs
structured JSON for the Intel Scout agent to process.

Sources:
  - CISA KEV  (Known Exploited Vulnerabilities)
  - ThreatFox (IOCs from abuse.ch)
  - Feodo Tracker (C2 IPs from abuse.ch)
  - DFIR Report (RSS feed of intrusion reports)
  - LOLBAS     (Living Off The Land Binaries and Scripts)
  - LOLDrivers (Vulnerable and malicious drivers)

Usage:
    python3 fetch_intel.py [--days N] [--output FILE]

Output is a JSON document with per-source results, IOC counts, and errors.
Upload this script as a payload to the central org:
    limacharlie payload create --name mdr-fetch-intel \\
        --path fetch_intel.py --oid <central-oid>
"""

import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone


def _ctx():
    """Return a permissive SSL context for public HTTPS endpoints."""
    ctx = ssl.create_default_context()
    return ctx


def fetch_url(url, method="GET", data=None, headers=None, timeout=30):
    """Fetch *url* and return the decoded body (str). Raises on HTTP errors."""
    headers = headers or {}
    req = urllib.request.Request(url, method=method, headers=headers)
    if data is not None:
        if isinstance(data, str):
            data = data.encode()
        req.data = data
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as resp:
        return resp.read().decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Individual source fetchers
# ---------------------------------------------------------------------------

def fetch_cisa_kev(days):
    """Return CISA KEV entries added in the last *days* days."""
    body = fetch_url(
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    )
    catalog = json.loads(body)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    recent = []
    for vuln in catalog.get("vulnerabilities", []):
        if vuln.get("dateAdded", "") >= cutoff:
            recent.append({
                "cve": vuln.get("cveID"),
                "vendor": vuln.get("vendorProject"),
                "product": vuln.get("product"),
                "name": vuln.get("vulnerabilityName"),
                "description": vuln.get("shortDescription"),
                "date_added": vuln.get("dateAdded"),
                "due_date": vuln.get("dueDate"),
                "known_ransomware": vuln.get("knownRansomwareCampaignUse"),
            })

    return {
        "source_url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
        "total_in_catalog": len(catalog.get("vulnerabilities", [])),
        "recent_entries": len(recent),
        "entries": recent,
    }


def fetch_threatfox(days):
    """Return ThreatFox IOCs published in the last *days* days."""
    payload = json.dumps({"query": "get_iocs", "days": days})
    body = fetch_url(
        "https://threatfox-api.abuse.ch/api/v1/",
        method="POST",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    data = json.loads(body)

    iocs = []
    for entry in (data.get("data") or []):
        iocs.append({
            "ioc": entry.get("ioc"),
            "ioc_type": entry.get("ioc_type"),
            "threat_type": entry.get("threat_type"),
            "malware": entry.get("malware_printable"),
            "confidence": entry.get("confidence_level"),
            "first_seen": entry.get("first_seen_utc"),
            "tags": entry.get("tags"),
            "reference": entry.get("reference"),
        })

    return {
        "source_url": "https://threatfox.abuse.ch/",
        "query_status": data.get("query_status"),
        "total_iocs": len(iocs),
        "iocs": iocs,
    }


def fetch_feodo():
    """Return recommended-blocklist C2 IPs from Feodo Tracker."""
    body = fetch_url(
        "https://feodotracker.abuse.ch/downloads/ipblocklist_recommended.txt"
    )
    ips = []
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ips.append(line)

    return {
        "source_url": "https://feodotracker.abuse.ch/",
        "total_ips": len(ips),
        "ips": ips,
    }


def fetch_dfir_report():
    """Return recent DFIR Report articles from the RSS feed."""
    body = fetch_url("https://thedfirreport.com/feed/")
    root = ET.fromstring(body)

    articles = []
    for item in root.iter("item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pub_date = item.findtext("pubDate", "")
        description = item.findtext("description", "")
        # Strip HTML tags from description (rough)
        import re
        description = re.sub(r"<[^>]+>", "", description).strip()
        if len(description) > 500:
            description = description[:500] + "..."
        articles.append({
            "title": title,
            "url": link,
            "published": pub_date,
            "summary": description,
        })

    return {
        "source_url": "https://thedfirreport.com/",
        "total_articles": len(articles),
        "articles": articles[:20],  # cap at 20 most recent
    }


def fetch_lolbas():
    """Return LOLBAS entries (binaries, scripts, libraries)."""
    body = fetch_url("https://lolbas-project.github.io/api/lolbas.json")
    entries = json.loads(body)

    results = []
    for entry in entries:
        results.append({
            "name": entry.get("Name"),
            "description": entry.get("Description"),
            "type": entry.get("Type"),
            "paths": entry.get("Full_Path") or entry.get("Paths"),
            "commands": [
                {
                    "command": cmd.get("Command"),
                    "description": cmd.get("Description"),
                    "category": cmd.get("Category"),
                    "mitre_id": cmd.get("MitreID"),
                }
                for cmd in (entry.get("Commands") or [])
            ],
            "detection": entry.get("Detection"),
        })

    return {
        "source_url": "https://lolbas-project.github.io/",
        "total_entries": len(results),
        "entries": results,
    }


def fetch_loldrivers():
    """Return LOLDrivers entries (vulnerable and malicious drivers)."""
    body = fetch_url("https://www.loldrivers.io/api/drivers.json")
    drivers = json.loads(body)

    results = []
    for driver in drivers:
        hashes = {}
        for sample in (driver.get("KnownVulnerableSamples") or []):
            for algo in ("SHA256", "SHA1", "MD5"):
                if sample.get(algo):
                    hashes.setdefault(algo.lower(), []).append(sample[algo])

        results.append({
            "id": driver.get("Id"),
            "category": driver.get("Category"),
            "commands": [
                cmd.get("Command") for cmd in (driver.get("Commands") or [])
            ],
            "tags": driver.get("Tags"),
            "hashes": hashes,
            "detection_rules": [
                rule.get("type") for rule in (driver.get("Detection") or [])
            ],
        })

    return {
        "source_url": "https://www.loldrivers.io/",
        "total_drivers": len(results),
        "drivers": results,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fetch threat intelligence from public sources."
    )
    parser.add_argument(
        "--days", type=int, default=1,
        help="Look-back window in days (default: 1)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Write JSON to this file instead of stdout",
    )
    args = parser.parse_args()

    results = {
        "fetch_timestamp": datetime.now(timezone.utc).isoformat(),
        "lookback_days": args.days,
        "sources": {},
    }

    fetchers = [
        ("cisa_kev", lambda: fetch_cisa_kev(max(args.days, 7))),
        ("threatfox", lambda: fetch_threatfox(args.days)),
        ("feodo_tracker", lambda: fetch_feodo()),
        ("dfir_report", lambda: fetch_dfir_report()),
        ("lolbas", lambda: fetch_lolbas()),
        ("loldrivers", lambda: fetch_loldrivers()),
    ]

    for name, fetcher in fetchers:
        try:
            results["sources"][name] = fetcher()
            results["sources"][name]["status"] = "ok"
        except Exception as exc:
            results["sources"][name] = {
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
            }

    # Summary counts
    summary = {"sources_ok": 0, "sources_error": 0, "total_iocs": 0}
    for src in results["sources"].values():
        if src.get("status") == "ok":
            summary["sources_ok"] += 1
            summary["total_iocs"] += (
                src.get("total_iocs", 0)
                + src.get("total_ips", 0)
                + src.get("recent_entries", 0)
            )
        else:
            summary["sources_error"] += 1
    results["summary"] = summary

    output = json.dumps(results, indent=2, default=str)
    if args.output:
        with open(args.output, "w") as fh:
            fh.write(output)
        print(f"Wrote {len(output)} bytes to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
