"""Least-privilege candidate keys; org deletion also revokes partial creations."""

from .local_cli import ControlError
from .organization import unwrap

PERMISSIONS = {
    "hive-preserve-update": ["org.get", "lookup.get", "lookup.get.mtd", "lookup.set", "lookup.set.mtd"],
    "search-complete-export": ["org.get", "sensor.list", "sensor.get", "insight.evt.get"],
    "webhook-production-routing": [
        "org.get",
        "sensor.list",
        "sensor.get",
        "insight.evt.get",
        "cloudsensor.get",
        "cloudsensor.get.mtd",
        "cloudsensor.set",
        "cloudsensor.set.mtd",
        "dr.list",
        "dr.set",
        "output.list",
        "output.set",
        "ikey.list",
    ],
}


def create(cli, journal, trial, oid, scenario):
    name = "candidate-" + trial
    intent = journal.intent(trial, "api_key", name, {"oid": oid})
    raw = unwrap(
        cli.invoke(
            ["api-key", "create", "--name", name, "--permissions", ",".join(PERMISSIONS[scenario])], oid
        )
    )
    key = next((raw.get(k) for k in ("api_key", "secret", "key") if isinstance(raw.get(k), str)), None)
    if not key:
        raise ControlError("key creation returned no secret")
    entries = cli.invoke(["api-key", "list"], oid)
    hashes = [h for h, v in entries.items() if v.get("name", v.get("key_name")) == name]
    if len(hashes) != 1:
        raise ControlError("cannot resolve created key identity")
    journal.acquired(intent, hashes[0], {"oid": oid})
    return key


def cleanup(cli, journal, resource):
    oid = resource["handle"]["oid"]
    entries = cli.invoke(["api-key", "list"], oid)
    matches = [h for h, v in entries.items() if v.get("name", v.get("key_name")) == resource["name"]]
    for key_hash in matches:
        if resource["resource_id"] and key_hash != resource["resource_id"]:
            raise ControlError("key identity mismatch")
        cli.invoke(["api-key", "delete", "--key-hash", key_hash, "--confirm"], oid)
    journal.cleaned(resource["intent"])
