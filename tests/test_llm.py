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


def test_gives_up_after_the_last_attempt(monkeypatch):
    c = client(monkeypatch, [ConnectionResetError()] * llm.ATTEMPTS)
    with pytest.raises(ConnectionResetError):
        c.complete("s", "u", "t")


def http_error(code):
    return llm.urllib.error.HTTPError("u", code, "x", {}, io.BytesIO(b""))


def test_proxy_405_is_retried_but_a_bad_key_is_final(monkeypatch):
    c = client(monkeypatch, [http_error(405), http_error(503), OK])
    assert c.complete("s", "u", "t")["response_id"] == "r1"
    c = client(monkeypatch, [http_error(401), OK])
    with pytest.raises(llm.urllib.error.HTTPError):
        c.complete("s", "u", "t")
