import os
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv
from upstash_vector import Index, Vector

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)

def test_upstash():
    if not os.getenv("UPSTASH_VECTOR_REST_URL") or not os.getenv("UPSTASH_VECTOR_REST_TOKEN"):
        pytest.fail(
            "Variables Upstash manquantes (UPSTASH_VECTOR_REST_URL / UPSTASH_VECTOR_REST_TOKEN). "
            "Renseigne-les dans le fichier .env (copié depuis .env.example)."
        )

    index = Index(
        url=os.getenv("UPSTASH_VECTOR_REST_URL"), 
        token=os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    )

    vector_id = f"test-index-{uuid.uuid4()}"
    
    result = index.upsert(
        vectors=[
            Vector(
                id=vector_id,
                data="exemple de texte index",
                metadata={"test": "index"},
            )
        ]
    )
    assert result is not None
    
    index.delete(ids=[vector_id])