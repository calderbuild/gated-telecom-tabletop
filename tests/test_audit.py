import json

from tabletop.audit import AuditLog, verify


def test_chain_verifies_and_detects_tampering(tmp_path):
    path = tmp_path / "log.jsonl"
    log = AuditLog(path)
    for i in range(5):
        log.append("claim", n=i, text="x" * i)
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
