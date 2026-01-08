from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from rag_tool import bootstrap_env


@dataclass(frozen=True)
class ChatStoreConfig:
    prefix: str = "portfolio-chat:"
    ttl_seconds: int | None = 60 * 60 * 24 * 14  # 14 days


def _load_config() -> ChatStoreConfig:
    prefix = os.getenv("CHAT_STORE_PREFIX", "portfolio-chat:")
    ttl_raw = os.getenv("CHAT_STORE_TTL_SECONDS", "")
    ttl: int | None

    if ttl_raw.strip() == "":
        ttl = 60 * 60 * 24 * 14
    else:
        try:
            ttl = int(ttl_raw)
        except ValueError:
            ttl = 60 * 60 * 24 * 14

    if ttl <= 0:
        ttl = None

    return ChatStoreConfig(prefix=prefix, ttl_seconds=ttl)


def _make_redis_client():
    # Imported lazily so the app can still run without the bonus dependency.
    from upstash_redis import Redis

    return Redis.from_env()


def _key(conversation_id: str) -> str:
    cfg = _load_config()
    return f"{cfg.prefix}{conversation_id}".strip()


def load_chat_state(conversation_id: str) -> dict[str, Any] | None:
    """Return saved state or None if not found / not configured.

    State schema:
      {"messages": [{"role": "user"|"assistant", "content": str}, ...],
       "previous_response_id": str|None}
    """

    bootstrap_env()

    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        return None

    redis = _make_redis_client()
    raw = redis.get(_key(conversation_id))
    if raw is None:
        return None

    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")

    if not isinstance(raw, str) or raw.strip() == "":
        return None

    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(obj, dict):
        return None

    return obj


def save_chat_state(
    conversation_id: str,
    *,
    messages: list[dict[str, str]],
    previous_response_id: str | None,
) -> None:
    """Persist the full chat state (best-effort; no-op if not configured)."""

    bootstrap_env()

    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        return

    cfg = _load_config()
    redis = _make_redis_client()

    payload = json.dumps(
        {
            "messages": messages,
            "previous_response_id": previous_response_id,
        },
        ensure_ascii=False,
    )

    key = _key(conversation_id)
    redis.set(key, payload)
    if cfg.ttl_seconds is not None:
        redis.expire(key, cfg.ttl_seconds)
