from __future__ import annotations

from pathlib import Path

from agents import Agent, ModelSettings, function_tool

from rag_tool import bootstrap_env, format_results, load_rag_config, make_index


@function_tool
def retrieve_profile_context(query: str, top_k: int = 5) -> str:
    """Retrieve relevant profile context from the Upstash Vector index.

    Use this tool whenever the user asks about the profile (projects, experiences,
    skills, education, contact). It returns short excerpts plus metadata.
    """

    project_root = Path(__file__).resolve().parent
    cfg = load_rag_config(project_root)
    index = make_index(cfg)

    results = index.query(
        data=query,
        top_k=top_k,
        include_metadata=True,
        include_data=True,
        namespace=cfg.namespace or "",
    )

    return format_results(results)


def build_agent() -> Agent[None]:
    bootstrap_env(Path(__file__).resolve().parent)

    instructions = (
        "Tu es un assistant qui répond aux questions sur le profil (portfolio) de l'utilisateur.\n"
        "Quand une question concerne le profil (expériences, projets, compétences, formation, contact), "
        "utilise l'outil retrieve_profile_context pour récupérer des extraits pertinents, puis répond en français "
        "en t'appuyant sur ces extraits.\n"
        "Si l'information n'est pas dans les extraits, dis-le clairement au lieu d'inventer.\n"
        "Réponse concise, structurée en puces si nécessaire."
    )

    return Agent(
        name="portfolio-agent",
        instructions=instructions,
        model="gpt-4.1-nano",
        model_settings=ModelSettings(temperature=0.2),
        tools=[retrieve_profile_context],
    )
