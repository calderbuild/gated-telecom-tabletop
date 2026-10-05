from tabletop.twin import Twin, check

S1_INV = [{"metric": f"emergency_reachable.{r}", "op": "==", "value": True} for r in ("R1", "R2", "R3")] + [
    {"metric": "pct_sites_served", "op": "==", "value": 100.0}]
S3_INV = [{"metric": "legit_pass_rate", "op": ">=", "value": 0.99}, {"metric": "fraud_block_rate", "op": "==", "value": 1.0}]
S2_INV = [{"metric": "leak_count", "op": "==", "value": 0}, {"metric": "benign_success_rate", "op": ">=", "value": 0.95}]
CHG1 = {"change_id": "CHG-1", "core": "A", "protection_limit": 50, "remove_route_filter": True}


def test_s1_change_breaks_emergency_routing_and_rollback_restores_it():
    t = Twin()
    assert check(t.metrics(), S1_INV)["holds"]
    after = t.act("apply_change", CHG1)["after"]
    assert after["emergency_reachable.R2"] is False and after["pct_sites_served"] == 60.0
    assert t.act("rollback_change", {"change_id": "CHG-1"})["error"] is None
    assert check(t.metrics(), S1_INV)["holds"]


def test_s1_wilting_restores_reachability_before_rollback():
    t = Twin()
    t.act("apply_change", CHG1)
    assert t.act("wilt_sites", {"region": "R2"})["after"]["emergency_reachable.R2"] is True


def test_s1_wilting_a_healthy_region_is_an_error_not_a_noop():
    assert Twin().act("wilt_sites", {"region": "R1"})["error"]


def test_s3_v2_locks_out_legit_users_and_unblocking_everyone_fails_the_invariant():
    t = Twin()
    t.act("deploy_model", {"version": "v2"})
    m = t.metrics()
    assert m["legit_pass_rate"] < 0.8 and m["fraud_block_rate"] == 1.0
    t.act("set_threshold", {"value": 2.0})
    assert not check(t.metrics(), S3_INV)["holds"]  # fraud gets through


def test_s3_rollback_or_review_queue_restores_both_rates():
    for verb, params in (("rollback_model", {"version": "v1"}), ("enable_review_queue", {})):
        t = Twin()
        t.act("deploy_model", {"version": "v2"})
        t.act(verb, params)
        assert check(t.metrics(), S3_INV)["holds"], verb


def test_s2_turning_the_bot_off_contains_but_does_not_restore_service():
    t = Twin()
    t.act("set_scope", {"scope": "all"})
    assert t.metrics()["leak_count"] == 14
    t.act("disable_tool", {})
    m = t.metrics()
    assert m["leak_count"] == 0 and not check(m, S2_INV)["holds"]
    t.act("restore_scope", {"scope": "own_account"})
    assert check(t.metrics(), S2_INV)["holds"]


def test_unknown_params_are_reported():
    assert Twin().act("rollback_change", {"change_id": "nope"})["error"]
