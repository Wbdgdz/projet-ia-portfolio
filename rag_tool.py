from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from upstash_vector import Index


@dataclass(frozen=True)
class RagConfig:
    url: str
    token: str
    namespace: str | None = None


def _apply_streamlit_secrets_to_env() -> None:
    try:
        import streamlit as st  # type: ignore
    except Exception:
        return

    try:
        secrets = st.secrets
    except Exception:
        return

    for key in (
        "OPENAI_API_KEY",
        "UPSTASH_VECTOR_REST_URL",
        "UPSTASH_VECTOR_REST_TOKEN",
        "UPSTASH_VECTOR_NAMESPACE",
    ):
        if os.getenv(key):
            continue
        try:
            if key in secrets and secrets[key] is not None:
                os.environ[key] = str(secrets[key])
        except Exception:
            continue


def bootstrap_env(project_root: Path | None = None) -> None:
    root = project_root or Path(__file__).resolve().parent
    load_dotenv(dotenv_path=root / ".env", override=False)
    _apply_streamlit_secrets_to_env()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(
            f"Missing env var: {name}. Fill it in .env (copied from .env.example) or set it via Streamlit secrets."
        )
    return value


def load_rag_config(project_root: Path | None = None) -> RagConfig:
    root = project_root or Path(__file__).resolve().parent
    bootstrap_env(root)

    url = _require_env("UPSTASH_VECTOR_REST_URL")
    token = _require_env("UPSTASH_VECTOR_REST_TOKEN")

    namespace = os.getenv("UPSTASH_VECTOR_NAMESPACE")
    if namespace is not None and namespace.strip() == "":
        namespace = None

    return RagConfig(url=url, token=token, namespace=namespace)


def make_index(cfg: RagConfig) -> Index:
    if not (cfg.url.startswith("https://") or cfg.url.startswith("http://")):
        raise RuntimeError(
            "UPSTASH_VECTOR_REST_URL must start with https:// (or http://)."
        )
    return Index(url=cfg.url, token=cfg.token)


def format_results(results, max_chars: int = 3500) -> str:
    if not results:
        return "Aucun résultat dans la base de connaissances."

    parts: list[str] = ["Résultats RAG (extraits) :"]
    for i, r in enumerate(results, start=1):
        heading = None
        source = None
        if getattr(r, "metadata", None):
            source = r.metadata.get("source_file")
            hp = r.metadata.get("heading_path")
            if isinstance(hp, list) and hp:
                heading = " > ".join(str(x) for x in hp)

        header_bits = [f"{i}) score={getattr(r, 'score', None):.3f}"]
        if source:
            header_bits.append(f"source={source}")
        if heading:
            header_bits.append(f"section={heading}")
        parts.append(" | ".join(header_bits))

        snippet = (getattr(r, "data", None) or "").strip()
        if snippet:
            parts.append(snippet)
        parts.append("---")

        if sum(len(p) + 1 for p in parts) > max_chars:
            parts.append("(… tronqué …)")
            break

    return "\n".join(parts).strip()
