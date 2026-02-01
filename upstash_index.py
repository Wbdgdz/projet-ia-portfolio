from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from upstash_vector import Index, Vector


def require_env(name: str) -> str:
    """Return the required env var or exit with a clear message."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise SystemExit(
            f"Missing env var: {name}. Fill it in .env (copied from .env.example)."
        )
    return value


def _normalize_optional(value: str | None) -> str | None:
    """Normalize empty strings to None for optional args/env vars."""
    if value is None or value.strip() == "":
        return None
    return value


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file into a list of dicts with validation."""
    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"Invalid JSON on line {line_no} in {path}: {e}") from e
    return items


def batched(seq: list[Any], batch_size: int) -> list[list[Any]]:
    """Split a list into fixed-size batches."""
    return [seq[i : i + batch_size] for i in range(0, len(seq), batch_size)]


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments for indexing."""
    parser = argparse.ArgumentParser(
        description="Index chunks.jsonl into an Upstash Vector index (uses REST URL/token from .env)."
    )
    parser.add_argument(
        "--chunks",
        default="chunks.jsonl",
        help="Path to chunks.jsonl produced by chunk_data.py",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="How many vectors to upsert per request",
    )
    parser.add_argument(
        "--namespace",
        default=None,
        help="Optional Upstash namespace to write into (default: none)",
    )
    parser.add_argument(
        "--id-prefix",
        default="",
        help="Optional prefix added to every chunk id (useful to avoid collisions)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and show what would be uploaded, without calling Upstash",
    )
    return parser.parse_args()


def _resolve_namespace(arg_value: str | None) -> str | None:
    """Resolve namespace from CLI arg or environment."""
    if arg_value is None:
        return _normalize_optional(os.getenv("UPSTASH_VECTOR_NAMESPACE"))
    return _normalize_optional(arg_value)


def _validate_index_url(url: str) -> None:
    """Validate Upstash REST URL format."""
    if not (url.startswith("https://") or url.startswith("http://")):
        raise SystemExit(
            "UPSTASH_VECTOR_REST_URL must start with https:// (or http://). "
            "Copy the REST URL from your Upstash Vector index."
        )


def _load_chunks(repo_root: Path, chunks_arg: str) -> list[dict[str, Any]]:
    """Load and validate chunks from a JSONL file."""
    chunks_path = (repo_root / chunks_arg).resolve()
    if not chunks_path.exists():
        raise SystemExit(
            f"Chunks file not found: {chunks_path}. Run: python chunk_data.py --out chunks.jsonl"
        )

    items = iter_jsonl(chunks_path)
    if not items:
        raise SystemExit(f"No chunks found in {chunks_path}")
    return items


def _build_vectors(items: list[dict[str, Any]], id_prefix: str) -> list[Vector]:
    """Convert chunk dicts into Upstash Vector objects."""
    vectors: list[Vector] = []
    for obj in items:
        chunk_id = str(obj.get("id", "")).strip()
        content = str(obj.get("content", "")).strip()
        if not chunk_id or not content:
            raise SystemExit(
                f"Invalid chunk entry (missing id/content): {obj.get('id')}"
            )

        metadata = {
            "source_file": obj.get("source_file"),
            "heading_path": obj.get("heading_path"),
        }
        vectors.append(
            Vector(
                id=f"{id_prefix}{chunk_id}",
                data=content,
                metadata=metadata,
            )
        )

    return vectors


def main() -> int:
    args = _parse_args()

    repo_root = Path(__file__).resolve().parent
    dotenv_path = repo_root / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=True)

    url = require_env("UPSTASH_VECTOR_REST_URL")
    token = require_env("UPSTASH_VECTOR_REST_TOKEN")

    namespace = _resolve_namespace(args.namespace)
    _validate_index_url(url)

    items = _load_chunks(repo_root, args.chunks)
    vectors = _build_vectors(items, args.id_prefix)

    if args.dry_run:
        print(f"Dry run: would upsert {len(vectors)} vectors")
        print(f"Index URL: {url}")
        if namespace:
            print(f"Namespace: {namespace}")
        print(f"First id: {vectors[0].id}")
        return 0

    index = Index(url=url, token=token)

    total = 0
    for batch_no, batch in enumerate(batched(vectors, args.batch_size), start=1):
        if namespace:
            index.upsert(vectors=batch, namespace=namespace)
        else:
            index.upsert(vectors=batch)
        total += len(batch)
        print(f"Batch {batch_no}: upserted {len(batch)} (total {total})")

    print(f"Done: upserted {total} vectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
