from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from upstash_vector import Index, Vector


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise SystemExit(
            f"Missing env var: {name}. Fill it in .env (copied from .env.example)."
        )
    return value


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
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
    return [seq[i : i + batch_size] for i in range(0, len(seq), batch_size)]


def main() -> int:
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
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    dotenv_path = repo_root / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=True)

    url = require_env("UPSTASH_VECTOR_REST_URL")
    token = require_env("UPSTASH_VECTOR_REST_TOKEN")

    namespace = args.namespace
    if namespace is None:
        namespace = os.getenv("UPSTASH_VECTOR_NAMESPACE")
    if namespace is not None and namespace.strip() == "":
        namespace = None

    if not (url.startswith("https://") or url.startswith("http://")):
        raise SystemExit(
            "UPSTASH_VECTOR_REST_URL must start with https:// (or http://). "
            "Copy the REST URL from your Upstash Vector index."
        )

    chunks_path = (repo_root / args.chunks).resolve()
    if not chunks_path.exists():
        raise SystemExit(
            f"Chunks file not found: {chunks_path}. Run: python chunk_data.py --out chunks.jsonl"
        )

    items = iter_jsonl(chunks_path)
    if not items:
        raise SystemExit(f"No chunks found in {chunks_path}")

    vectors: list[Vector] = []
    for obj in items:
        chunk_id = str(obj.get("id", "")).strip()
        content = str(obj.get("content", "")).strip()
        if not chunk_id or not content:
            raise SystemExit(
                f"Invalid chunk entry (missing id/content): {obj.get('id')} from {chunks_path}"
            )

        metadata = {
            "source_file": obj.get("source_file"),
            "heading_path": obj.get("heading_path"),
        }
        vectors.append(
            Vector(
                id=f"{args.id_prefix}{chunk_id}",
                data=content,
                metadata=metadata,
            )
        )

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
            result = index.upsert(vectors=batch, namespace=namespace)
        else:
            result = index.upsert(vectors=batch)
        total += len(batch)
        print(f"Batch {batch_no}: upserted {len(batch)} (total {total})")
        _ = result

    print(f"Done: upserted {total} vectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
