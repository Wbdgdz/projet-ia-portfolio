from __future__ import annotations

from pathlib import Path
import re

from agents import Agent, ModelSettings, function_tool

from rag_tool import bootstrap_env, format_results, load_rag_config, make_index


def retrieve_profile_context_impl(query: str, top_k: int = 5) -> str:
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


def list_profile_sections_impl() -> str:
    data_dir = Path(__file__).resolve().parent / "data"
    if not data_dir.exists():
        return "Aucune donnée trouvée (dossier data/ manquant)."

    heading_re = re.compile(r"^(#{1,3})\s+(.*)\s*$")
    lines: list[str] = ["Sections disponibles :"]

    for md_path in sorted(data_dir.glob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
        except Exception:
            continue

        headings: list[str] = []
        for raw in text.splitlines():
            m = heading_re.match(raw)
            if not m:
                continue
            level = len(m.group(1))
            title = m.group(2).strip()
            if not title:
                continue
            if level == 1:
                headings.append(title)
            elif level == 2:
                headings.append(f"- {title}")

        if headings:
            lines.append(f"\n{md_path.name}:")
            lines.extend(headings)

    return "\n".join(lines).strip()


@function_tool
def list_profile_sections() -> str:
    """List the available profile sections (from local markdown headings)."""

    return list_profile_sections_impl()


@function_tool
def retrieve_profile_context(query: str, top_k: int = 5) -> str:
    """Retrieve relevant profile context from the Upstash Vector index.

    Use this tool whenever the user asks about the profile (projects, experiences,
    skills, education, contact). It returns short excerpts plus metadata.
    """

    return retrieve_profile_context_impl(query=query, top_k=top_k)


def build_agent() -> Agent[None]:
    bootstrap_env(Path(__file__).resolve().parent)

    instructions = (
        "Tu t'appelles Dawei David Zhou et tu réponds à l'utilisateur en parlant à la première personne (" 
        "comme si tu étais Dawei).\n"
        "Quand une question concerne ton profil (expériences, projets, compétences, formation, contact), "
        "utilise l'outil retrieve_profile_context pour récupérer des extraits pertinents, puis répond en français "
        "en t'appuyant strictement sur ces extraits.\n"
        "Si l'utilisateur demande ce que tu peux couvrir, utilise l'outil list_profile_sections.\n"
        "Si l'information n'est pas dans les extraits, dis-le clairement au lieu d'inventer.\n"
        "Réponse concise, naturelle et professionnelle; utilise des puces si nécessaire."
    )

    return Agent(
        name="portfolio-agent",
        instructions=instructions,
        model="gpt-4.1-nano",
        model_settings=ModelSettings(temperature=0.2),
        tools=[retrieve_profile_context, list_profile_sections],
    )
