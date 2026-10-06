from tabletop.gate import check

TEXT = "In the case of any unplanned interruption the Licensee shall inform the TDRA as soon as possible."
CHUNKS = {
    "UAE-LIC#1": {"chunk_id": "UAE-LIC#1", "doc_id": "UAE-LIC", "text": TEXT},
    "CA-CRTC#1": {"chunk_id": "CA-CRTC#1", "doc_id": "CA-CRTC", "text": "Providers must notify the CRTC within two hours of a major outage."},
    "UAE-PRESS#1": {"chunk_id": "UAE-PRESS#1", "doc_id": "UAE-PRESS", "text": "Calls failed after a planned system update to improve network performance."},
}
MANIFEST = {
    "UAE-LIC": {"status": "VERIFIED", "layer": "uae-telecom"},
    "CA-CRTC": {"status": "VERIFIED", "layer": "global-precedent"},
    "UAE-PRESS": {"status": "SECONDARY", "layer": "uae-telecom"},
}
CTX = {
    "agent": "NOC", "mandate": {"verbs": {"notify": {}, "rollback_change": {}}}, "institutions": ["NOC", "REG", "EMS"],
    "retrieved": set(CHUNKS), "visible": {"S1-I1", "S1-I2"}, "chunks": CHUNKS, "manifest": MANIFEST,
    "rules": [{"doc_id": "CA-CRTC", "hours": 2}],
}
EV = [{"chunk_id": "UAE-LIC#1", "quote": "the Licensee shall inform the TDRA as soon as possible"}]


def claim(**kw):
    base = {"type": "action", "verb": "notify", "params": {"to": "REG"}, "inject_refs": ["S1-I2"], "evidence": EV}
    return {**base, **kw}


def test_valid_action_passes():
    assert check(claim(), CTX) == []


def test_quote_survives_line_breaks_and_curly_quotes():
    ev = [{"chunk_id": "UAE-LIC#1", "quote": "the Licensee  shall\ninform the TDRA as soon as possible."}]
    assert check(claim(evidence=ev), CTX) == []


def test_fabricated_quote_is_rejected():
    ev = [{"chunk_id": "UAE-LIC#1", "quote": "the Licensee shall inform the TDRA within two hours"}]
    assert any(r.startswith("NOT_VERBATIM") for r in check(claim(evidence=ev), CTX))


def test_quote_from_a_chunk_not_retrieved_is_rejected():
    ctx = {**CTX, "retrieved": {"CA-CRTC#1"}}
    assert any(r.startswith("NOT_RETRIEVED") for r in check(claim(), ctx))


def test_verb_outside_mandate_is_rejected():
    assert "MANDATE:issue_direction" in check(claim(verb="issue_direction"), CTX)


def test_unreleased_inject_is_rejected():
    assert "INJECT:S1-I4" in check(claim(inject_refs=["S1-I4"]), CTX)


def test_obligation_on_secondary_source_is_rejected():
    ev = [{"chunk_id": "UAE-PRESS#1", "quote": "Calls failed after a planned system update"}]
    reasons = check({"type": "obligation", "statement": "x", "inject_refs": ["S1-I1"], "evidence": ev}, CTX)
    assert any(r.startswith("NOT_VERIFIED") for r in reasons)


def test_deadline_must_come_from_the_rule_table():
    ob = {"type": "obligation", "statement": "notify", "inject_refs": ["S1-I1"], "evidence": EV, "deadline_hours": 2}
    assert any(r.startswith("DEADLINE") for r in check(ob, CTX))  # UAE text states no hours
    ev = [{"chunk_id": "CA-CRTC#1", "quote": "notify the CRTC within two hours of a major outage"}]
    assert check({**ob, "evidence": ev}, CTX) == []


def test_gap_global_example_must_be_global_and_verified():
    gap = {"type": "gap", "gap_type": "no_deadline", "statement": "x", "evidence": EV,
           "global_examples": [{"chunk_id": "CA-CRTC#1", "quote": "notify the CRTC within two hours"}]}
    assert check(gap, CTX) == []
    gap["global_examples"] = [{"chunk_id": "UAE-LIC#1", "quote": "inform the TDRA as soon as possible"}]
    assert any(r.startswith("NOT_GLOBAL") for r in check(gap, CTX))


def test_share_to_self_is_rejected():
    assert any(r.startswith("ROUTE") for r in check({"type": "share", "to": ["NOC"], "inject_refs": ["S1-I1"]}, CTX))


def test_malformed_model_shapes_are_rejected_not_raised():
    shapes = [
        claim(evidence="the Licensee shall inform the TDRA as soon as possible"),
        claim(evidence=[None]),
        claim(evidence=[{"chunk_id": ["UAE-LIC#1"], "quote": "the Licensee shall inform the TDRA"}]),
        claim(type=["action"]),
        claim(verb=["notify"]),
        claim(inject_refs="S1-I2"),
        claim(params={"to": ["REG"]}),
        {"type": "share", "to": "REG", "inject_refs": ["S1-I2"]},
        {"type": "gap", "gap_type": ["no_rule"], "inject_refs": ["S1-I2"], "evidence": EV},
    ]
    for c in shapes:
        assert check(c, CTX), c


def test_notify_to_self_or_unknown_is_a_route_error():
    assert any(r.startswith("ROUTE") for r in check(claim(params={"to": "NOC"}), CTX))
    assert any(r.startswith("ROUTE") for r in check(claim(params={"to": "FBI"}), CTX))


def test_notify_reaches_audiences_the_mandate_lists():
    ctx = {**CTX, "mandate": {"verbs": {"notify": {"params": {"to": "REG | customers"}}}}}
    assert check(claim(params={"to": "customers"}), ctx) == []
    assert any(r.startswith("ROUTE") for r in check(claim(params={"to": "EMS"}), ctx))


def test_malformed_obligation_evidence_is_rejected_not_a_crash():
    for ev in ([{"chunk_id": ["UAE-LIC#1"], "quote": "x"}], 5):
        c = {"type": "obligation", "owner": "NOC", "deadline_hours": 2, "inject_refs": ["S1-I2"], "evidence": ev}
        assert check(c, CTX)
