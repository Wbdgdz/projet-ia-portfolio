from __future__ import annotations

from typing import Any

import chat_store


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}
        self.expiries: dict[str, int] = {}

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, value: str):
        self.store[key] = value
        return "OK"

    def expire(self, key: str, ttl: int):
        self.expiries[key] = ttl
        return 1


def test_load_chat_state_returns_none_if_not_configured(monkeypatch):
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)

    assert chat_store.load_chat_state("abc") is None


def test_save_chat_state_noop_if_not_configured(monkeypatch):
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)

    # Should not raise
    chat_store.save_chat_state(
        "abc",
        messages=[{"role": "user", "content": "hi"}],
        previous_response_id=None,
    )


def test_roundtrip_chat_state_with_fake_redis(monkeypatch):
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://example")
    monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "token")
    monkeypatch.setenv("CHAT_STORE_PREFIX", "test:")
    monkeypatch.setenv("CHAT_STORE_TTL_SECONDS", "123")

    fake = FakeRedis()
    monkeypatch.setattr(chat_store, "_make_redis_client", lambda: fake)
    monkeypatch.setattr(chat_store, "_bootstrap_env", lambda: None)

    messages = [
        {"role": "user", "content": "salut"},
        {"role": "assistant", "content": "bonjour"},
    ]

    chat_store.save_chat_state("cid1", messages=messages, previous_response_id="resp_1")
    state: dict[str, Any] | None = chat_store.load_chat_state("cid1")

    assert state is not None
    assert state["messages"] == messages
    assert state["previous_response_id"] == "resp_1"

    assert fake.expiries["test:cid1"] == 123
