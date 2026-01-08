import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from agents import Agent, Runner, ModelSettings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)

def test_openai_agent_runs_ping_pong():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.fail(
            "OPENAI_API_KEY non défini. Renseigne-le dans le fichier .env (copié depuis .env.example)."
        )

    agent = Agent(
        name="ping-agent",
        instructions="Réponds uniquement avec le mot 'pong' (minuscules), sans ponctuation ni autre texte.",
        model="gpt-4.1-nano",
        model_settings=ModelSettings(temperature=0),
    )

    result = Runner.run_sync(agent, "ping")
    assert result.final_output.strip() == "pong"
