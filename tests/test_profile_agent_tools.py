from __future__ import annotations

from profile_agent import list_profile_sections_impl


def test_list_profile_sections_mentions_data_files():
    text = list_profile_sections_impl()

    # File names should be present if data/ exists
    assert "01_experiences.md" in text
    assert "02_projets.md" in text
    assert "03_competences.md" in text
