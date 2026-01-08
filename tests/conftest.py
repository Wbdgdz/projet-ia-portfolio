from __future__ import annotations

import sys
from pathlib import Path


# Ensure root-level modules (chunk_data.py, chat_store.py, etc.) are importable
# regardless of how pytest is invoked (venv, system Python, import mode, etc.).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
