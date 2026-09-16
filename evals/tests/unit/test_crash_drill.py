import json

from lc_eval.crash_drill import _crash_marker


def _resource(kind, name, number):
    return {
        "kind": kind,
        "name": name,
        "resource_id": f"id-{number}",
        "status": "active",
    }


def test_crash_marker_requires_a_fully_acquired_candidate_runtime(tmp_path):
    marker = {
        "oid": "00000000-0000-4000-8000-000000000001",
        "resources": [
            _resource("org", "owned-org", 1),
            _resource("api_key", "owned-key", 2),
            _resource("docker_network", "trial-an", 3),
            _resource("docker_network", "trial-wn", 4),
            _resource("docker_container", "trial-agent", 5),
            _resource("docker_container", "trial-worker", 6),
            _resource("docker_container", "trial-ap", 7),
            _resource("docker_container", "trial-wp", 8),
        ],
    }
    path = tmp_path / "crash-created.json"
    path.write_text(json.dumps(marker))

    _, evidence = _crash_marker(path)
    assert evidence["valid"] is True
    assert evidence["candidate_container"] == "trial-agent"
    assert evidence["container_count"] == 4
    assert evidence["network_count"] == 2


def test_crash_marker_does_not_accept_partial_or_unacquired_resources(tmp_path):
    marker = {
        "oid": "00000000-0000-4000-8000-000000000001",
        "resources": [
            _resource("org", "owned-org", 1),
            _resource("api_key", "owned-key", 2),
            _resource("docker_network", "trial-an", 3),
            _resource("docker_container", "trial-agent", 4),
        ],
    }
    marker["resources"][-1]["status"] = "creating"
    path = tmp_path / "crash-created.json"
    path.write_text(json.dumps(marker))

    _, evidence = _crash_marker(path)
    assert evidence["valid"] is False
    assert evidence["candidate_container"] is None
