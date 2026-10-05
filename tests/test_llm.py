import io
import json

import pytest

from tabletop import llm

OK = json.dumps({"id": "r1", "model": "m", "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]}).encode()


def client(monkeypatch, replies):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    seq = iter(replies)

    def urlopen(req, timeout):
        r = next(seq)
        if isinstance(r, Exception):
            raise r
        return io.BytesIO(r)

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    return llm.DeepSeek("m")


def test_reset_and_cut_body_are_retried(monkeypatch):
    c = client(monkeypatch, [ConnectionResetError(), OK[:20], OK])
    assert c.complete("s", "u", "t")["response_id"] == "r1"


def test_gives_up_after_four_attempts(monkeypatch):
    c = client(monkeypatch, [ConnectionResetError()] * 4)
    with pytest.raises(ConnectionResetError):
        c.complete("s", "u", "t")
