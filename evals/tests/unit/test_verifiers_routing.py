from lc_eval.verifiers.routing import verify_routing


def _facts():
    return {
        "expected_match_ids": ["match"],
        "expected_negative_ids": ["stage", "wrong-type"],
        "observed_ingestion_ids": ["match", "stage", "wrong-type"],
        "receiver_health": {"management_reachable": True, "receiver_ready": True, "positive_control_received": True},
        "observation_window": {"start": 1000, "end": 1180, "complete": True},
        "received_records": [{"payload": {"event": {"eval_event_id": "match"}}, "signature_valid": True, "received_at": 1100}],
        "baseline_output_before": {"name": "keep", "cat": "baseline"},
        "baseline_output_after": {"name": "keep", "cat": "baseline"},
    }


def test_routing_passes_fresh_signed_matches_and_bounded_negatives():
    assert all(result["status"] == "pass" for result in verify_routing({}, {}, {}, _facts()))


def test_routing_missing_health_cannot_pass_absence_or_missing_match():
    facts = _facts()
    facts.pop("receiver_health")
    facts["received_records"] = []
    statuses = {result["id"]: result["status"] for result in verify_routing({}, {}, {}, facts)}
    assert statuses["routing.receiver_health"] == "unknown"
    assert statuses["routing.matching_delivered"] == "unknown"
    assert statuses["routing.negatives_excluded"] == "unknown"


def test_routing_partial_health_without_positive_control_is_unknown():
    facts = _facts()
    facts["receiver_health"] = {"management_reachable": True, "receiver_ready": True}
    facts["received_records"] = []
    statuses = {result["id"]: result["status"] for result in verify_routing({}, {}, {}, facts)}
    assert statuses["routing.receiver_health"] == "unknown"
    assert statuses["routing.negatives_excluded"] == "unknown"


def test_routing_ignores_stale_and_bad_signatures_but_fails_fresh_negative():
    facts = _facts()
    facts["received_records"] = [
        {"eval_event_id": "match", "signature_valid": True, "received_at": 900},
        {"eval_event_id": "match", "signature_valid": False, "received_at": 1100},
        {"eval_event_id": "stage", "signature_valid": True, "received_at": 1101},
    ]
    statuses = {result["id"]: result["status"] for result in verify_routing({}, {}, {}, facts)}
    assert statuses["routing.matching_delivered"] == "fail"
    assert statuses["routing.negatives_excluded"] == "fail"
