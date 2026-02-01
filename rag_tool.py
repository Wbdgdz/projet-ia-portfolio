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
    """Load Streamlit secrets into env vars if present."""
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
        "UPSTASH_REDIS_REST_URL",
        "UPSTASH_REDIS_REST_TOKEN",
    ):
        if os.getenv(key):
            continue
        try:
            if key in secrets and secrets[key] is not None:
                os.environ[key] = str(secrets[key])
        except Exception:
            continue


def bootstrap_env(project_root: Path | None = None) -> None:
    """Load .env and Streamlit secrets into environment variables."""
    root = project_root or Path(__file__).resolve().parent
    load_dotenv(dotenv_path=root / ".env", override=False)
    _apply_streamlit_secrets_to_env()


def _require_env(name: str) -> str:
    """Return the required env var or raise a RuntimeError."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(
            f"Missing env var: {name}. Fill it in .env (copied from .env.example) or set it via Streamlit secrets."
        )
    return value


def _normalize_optional(value: str | None) -> str | None:
    """Normalize empty strings to None for optional env vars."""
    if value is None or value.strip() == "":
        return None
    return value


def load_rag_config(project_root: Path | None = None) -> RagConfig:
    """Load and validate RAG configuration from environment variables."""
    root = project_root or Path(__file__).resolve().parent
    bootstrap_env(root)

    url = _require_env("UPSTASH_VECTOR_REST_URL")
    token = _require_env("UPSTASH_VECTOR_REST_TOKEN")

    namespace = _normalize_optional(os.getenv("UPSTASH_VECTOR_NAMESPACE"))

    return RagConfig(url=url, token=token, namespace=namespace)


def make_index(cfg: RagConfig) -> Index:
    """Create an Upstash Vector index client from config."""
    if not (cfg.url.startswith("https://") or cfg.url.startswith("http://")):
        raise RuntimeError(
            "UPSTASH_VECTOR_REST_URL must start with https:// (or http://)."
        )
    return Index(url=cfg.url, token=cfg.token)


def _extract_source_and_heading(metadata) -> tuple[str | None, str | None]:
    """Extract source file and heading path from metadata."""
    if not metadata:
        return None, None

    source = metadata.get("source_file")
    heading = None
    heading_path = metadata.get("heading_path")
    if isinstance(heading_path, list) and heading_path:
        heading = " > ".join(str(x) for x in heading_path)

    return source, heading


def _format_header(i: int, score: float | None, source: str | None, heading: str | None) -> str:
    """Format a single result header line."""
    header_bits = [f"{i}) score={score:.3f}"]
    if source:
        header_bits.append(f"source={source}")
    if heading:
        header_bits.append(f"section={heading}")
    return " | ".join(header_bits)


def _format_citation(i: int, source: str | None, heading: str | None) -> str | None:
    """Format a human-readable citation entry."""
    if not (source or heading):
        return None
    label = source or "source_inconnu"
    if heading:
        label = f"{label} > {heading}"
    return f"[{i}] {label}"


def format_results(results, max_chars: int = 3500) -> str:
    """Format vector search results into a readable text block."""
    if not results:
        return "Aucun résultat dans la base de connaissances."

    parts: list[str] = ["Résultats RAG (extraits) :"]
    citations: list[str] = []
    for i, r in enumerate(results, start=1):
        source, heading = _extract_source_and_heading(getattr(r, "metadata", None))
        parts.append(
            _format_header(
                i,
                getattr(r, "score", None),
                source,
                heading,
            )
        )

        snippet = (getattr(r, "data", None) or "").strip()
        if snippet:
            parts.append(snippet)
        parts.append("---")

        citation = _format_citation(i, source, heading)
        if citation:
            citations.append(citation)

        if sum(len(p) + 1 for p in parts) > max_chars:
            parts.append("(… tronqué …)")
            break

    if citations:
        parts.append("Citations :")
        parts.extend(f"- {c}" for c in citations)

    return "\n".join(parts).strip()
