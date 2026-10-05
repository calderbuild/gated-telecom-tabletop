"""Hash-chained, append-only audit log (JSONL).

Each line is one event. Its hash is the SHA-256 of the canonical JSON of
{seq, prev_hash, type, data}; changing any byte of an earlier line breaks every
later link, and `verify` reports the first broken one.
"""

import hashlib
import json
from pathlib import Path

GENESIS = "0" * 64


def canonical(obj) -> bytes:
    return json.dumps(
        obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()


def sha256(obj) -> str:
    data = obj if isinstance(obj, bytes) else canonical(obj)
    return hashlib.sha256(data).hexdigest()


def event_hash(seq: int, prev_hash: str, type_: str, data: dict) -> str:
    return sha256({"seq": seq, "prev_hash": prev_hash, "type": type_, "data": data})


class AuditLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("")
        self.seq = 0
        self.prev = GENESIS
        self.events = []

    def append(self, type_: str, **data) -> dict:
        h = event_hash(self.seq, self.prev, type_, data)
        ev = {
            "seq": self.seq,
            "prev_hash": self.prev,
            "type": type_,
            "data": data,
            "hash": h,
        }
        with self.path.open("a") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        self.events.append(ev)
        self.seq += 1
        self.prev = h
        return ev


def load(path: Path) -> list[dict]:
    return [
        json.loads(line) for line in Path(path).read_text().split("\n") if line.strip()
    ]


def verify(path: Path) -> tuple[bool, str]:
    """Recompute the chain. Returns (ok, message naming the first broken link)."""
    prev = GENESIS
    try:
        events = load(path)
    except json.JSONDecodeError as e:
        return False, f"line {e.lineno}: not valid JSON"
    if not events:
        return False, "empty log"
    for i, ev in enumerate(events):
        if ev.get("seq") != i:
            return False, f"line {i + 1}: seq {ev.get('seq')} != {i}"
        if ev.get("prev_hash") != prev:
            return False, f"seq {i}: prev_hash does not match hash of seq {i - 1}"
        if event_hash(i, prev, ev["type"], ev["data"]) != ev.get("hash"):
            return False, f"seq {i}: content does not match its hash"
        prev = ev["hash"]
    return True, f"{len(events)} events, chain intact, head {prev[:16]}"
