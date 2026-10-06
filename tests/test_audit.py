import json

from tabletop.audit import AuditLog, verify


def test_chain_verifies_and_detects_tampering(tmp_path):
    path = tmp_path / "log.jsonl"
    log = AuditLog(path)
    for i in range(5):
        log.append("claim", n=i, text="x" * i)
    log.append("run_end")
    assert verify(path)[0]

    lines = path.read_text().splitlines()
    ev = json.loads(lines[2])
    ev["data"]["text"] = "edited"
    lines[2] = json.dumps(ev)
    path.write_text("\n".join(lines) + "\n")
    ok, msg = verify(path)
    assert not ok and "seq 2" in msg


def test_deleting_a_line_breaks_the_chain(tmp_path):
    path = tmp_path / "log.jsonl"
    log = AuditLog(path)
    for i in range(3):
        log.append("claim", n=i)
    lines = path.read_text().splitlines()
    path.write_text("\n".join([lines[0], lines[2]]) + "\n")
    assert not verify(path)[0]


def test_line_separator_inside_a_value_does_not_split_the_event(tmp_path):
    path = tmp_path / "log.jsonl"
    log = AuditLog(path)
    log.append("claim", text="before after")
    log.append("run_end")
    assert verify(path)[0]


def test_cut_tail_is_not_a_complete_log(tmp_path):
    path = tmp_path / "log.jsonl"
    log = AuditLog(path)
    log.append("claim", n=0)
    log.append("run_end")
    lines = path.read_text().splitlines()
    path.write_text(lines[0] + "\n")
    ok, msg = verify(path)
    assert not ok and "no run_end" in msg


def test_non_event_line_is_reported_not_raised(tmp_path):
    path = tmp_path / "log.jsonl"
    path.write_text("[1, 2]\n")
    assert not verify(path)[0]


def test_baseline_with_unparseable_reply_still_closes_its_log(tmp_path):
    from tabletop import engine

    class Garbled:
        name, model = "garbled", "m"

        def complete(self, system, user, tag):
            return {"text": "not json", "reasoning": None, "response_id": "r", "model": "m",
                    "usage": {}, "latency_s": 0, "finish_reason": "stop"}

    log = engine.baseline(engine.load_scenario("S1"), Garbled(), tmp_path / "b.jsonl")
    ok, msg = verify(log)
    assert ok, msg
