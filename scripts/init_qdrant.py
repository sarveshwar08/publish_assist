"""init qdrant collections needed

Add qdrant collection names when need be
"""

from __future__ import annotations

import argparse
import time
from typing import Iterable

from qdrant_client.http.models import Distance, VectorParams

from publish_assist.application.networks.embeddings import EmbeddingModelSingleton
from publish_assist.infra.db.qdrant import get_qdrant_client


COLLECTIONS = ["embedded_articles", "embedded_transcripts"]


def _wait_for_qdrant(max_wait_seconds: int = 60) -> None:
    client = get_qdrant_client()
    deadline = time.time() + max_wait_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            client.get_collections()
            return
        except Exception as e:
            last_error = e
            time.sleep(1)

    raise RuntimeError(f"Qdrant did not become ready in {max_wait_seconds}s: {last_error!s}")


def _ensure_collections(
    *,
    collection_names: Iterable[str],
    vector_size: int,
    recreate: bool,
) -> None:
    client = get_qdrant_client()
    vectors_config = VectorParams(size=vector_size, distance=Distance.COSINE)

    for name in collection_names:
        if recreate:
            client.recreate_collection(collection_name=name, vectors_config=vectors_config)
            continue

        exists = False
        try:
            exists = bool(client.collection_exists(collection_name=name))
        except Exception:
            try:
                client.get_collection(name)
                exists = True
            except Exception:
                exists = False

        if not exists:
            client.create_collection(collection_name=name, vectors_config=vectors_config)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="DROP and recreate collections",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=60,
        help="Seconds to wait for qdrant to become ready.",
    )
    args = parser.parse_args()

    _wait_for_qdrant(max_wait_seconds=int(args.wait))

    embedder = EmbeddingModelSingleton()
    _ensure_collections(
        collection_names=COLLECTIONS,
        vector_size=int(embedder.embedding_size),
        recreate=bool(args.recreate),
    )

    print(f"Qdrant collections ready: {', '.join(COLLECTIONS)}")


if __name__ == "__main__":
    main()
