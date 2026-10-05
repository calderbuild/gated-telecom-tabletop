"""Model access. The model only proposes; nothing it returns counts until the gate accepts it.

Providers:
  deepseek  OpenAI-compatible chat API (default), key DEEPSEEK_API_KEY
  replay    returns responses recorded in an earlier audit log, in order, so a run can be
            re-executed and its gate verdicts compared byte for byte
  mock      deterministic fixture for tests and selftest (see agents.mock_response)
"""

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from tabletop.audit import sha256

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-pro"


def load_env(path: Path):
    """Read KEY=VALUE lines from .env without executing anything (malformed lines are skipped)."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip().isidentifier() and key.strip() not in os.environ:
            os.environ[key.strip()] = value.strip().strip("'\"")


class DeepSeek:
    name = "deepseek"

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.key = os.environ.get("DEEPSEEK_API_KEY")
        if not self.key:
            raise SystemExit("DEEPSEEK_API_KEY is not set (put it in app/.env)")

    def complete(self, system: str, user: str, tag: str) -> dict:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 8000,
        }
        req = urllib.request.Request(
            DEEPSEEK_URL,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
            },
        )
        for attempt in range(4):
            t0 = time.time()
            try:
                resp = json.loads(urllib.request.urlopen(req, timeout=600).read())
                break
            except (urllib.error.URLError, TimeoutError) as e:
                status = getattr(e, "code", None)
                if attempt == 3 or (
                    status is not None and status < 500 and status != 429
                ):
                    raise
                time.sleep(5 * 2**attempt)
        msg = resp["choices"][0]["message"]
        return {
            "text": msg.get("content") or "",
            "reasoning": msg.get("reasoning_content") or "",
            "response_id": resp.get("id"),
            "model": resp.get("model", self.model),
            "usage": resp.get("usage", {}),
            "latency_s": round(time.time() - t0, 2),
            "finish_reason": resp["choices"][0].get("finish_reason"),
        }


class Replay:
    name = "replay"

    def __init__(self, events: list[dict]):
        self.calls = {}
        for ev in events:
            if ev["type"] == "model_call":
                self.calls.setdefault(ev["data"]["tag"], []).append(ev["data"])

    def complete(self, system: str, user: str, tag: str) -> dict:
        recorded = self.calls[tag].pop(0)
        if recorded["request_sha256"] != sha256({"system": system, "user": user}):
            raise SystemExit(
                f"replay diverged at {tag}: prompt differs from the recorded run"
            )
        return {
            k: recorded[k]
            for k in (
                "text",
                "reasoning",
                "response_id",
                "model",
                "usage",
                "latency_s",
                "finish_reason",
            )
        }


class Mock:
    name = "mock"
    model = "mock"

    def __init__(self, responder):
        self.responder = responder

    def complete(self, system: str, user: str, tag: str) -> dict:
        return {
            "text": self.responder(tag, user),
            "reasoning": "",
            "response_id": None,
            "model": "mock",
            "usage": {},
            "latency_s": 0.0,
            "finish_reason": "stop",
        }


def parse_json(text: str):
    """Parse the model's JSON object. Returns (obj, error)."""
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`").removeprefix("json").strip()
    try:
        obj = json.loads(t)
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"
    if not isinstance(obj, dict):
        return None, "top level is not an object"
    return obj, None
