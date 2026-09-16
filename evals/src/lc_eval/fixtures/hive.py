"""Seeded semantic fixture, independently read through the platform API."""

from copy import deepcopy
import hashlib
import json
from urllib.parse import quote


def set_record(cli, oid, hive, name, record):
    return cli.api(
        oid,
        "POST",
        f"hive/{hive}/{oid}/{quote(name, safe='')}/data",
        form={"data": json.dumps(record["data"]), "usr_mtd": json.dumps(record["usr_mtd"])},
    )


def snapshot(cli, oid, hive="lookup"):
    listing = cli.api(oid, "GET", f"hive/{hive}/{oid}")
    if not isinstance(listing, dict):
        raise ValueError("unsupported Hive listing")
    records = {}
    for name in listing:
        raw = cli.api(oid, "GET", f"hive/{hive}/{oid}/{quote(name, safe='')}/data")
        data = raw.get("data")
        if isinstance(data, str):
            data = json.loads(data)
        records[name] = {"data": data, "usr_mtd": raw.get("usr_mtd", {})}
    return records


def provision(cli, oid, seed):
    suffix = hashlib.sha256(str(seed).encode()).hexdigest()[:10]
    target = "asset-owners-" + suffix
    asset = "app-" + suffix[:5]
    records = {
        target: {
            "data": {
                "lookup_data": {
                    asset: {"owner": "infra", "tier": "critical", "notes": ["retain", "unicode: café"]},
                    "db-" + suffix[:5]: {"owner": "data", "tier": "standard"},
                }
            },
            "usr_mtd": {"enabled": False, "tags": ["eval", "preserve"], "comment": "Preserve this metadata"},
        },
        target + "-archive": {
            "data": {"lookup_data": {asset: {"owner": "archive", "tier": "retired"}}},
            "usr_mtd": {"enabled": True, "tags": ["archive"], "comment": "Unrelated record"},
        },
    }
    for name, record in records.items():
        set_record(cli, oid, "lookup", name, record)
    baseline = snapshot(cli, oid)
    expected = deepcopy(baseline)
    expected[target]["data"]["lookup_data"][asset]["owner"] = "platform-ops"
    return {
        "target_name": target,
        "target_asset_key": asset,
        "baseline_records": baseline,
        "expected_records": expected,
        "public": {"organization_id": oid, "target_record_name": target, "target_asset_key": asset},
    }
