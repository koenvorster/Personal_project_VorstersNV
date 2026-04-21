import pytest
from pathlib import Path
from ollama.skill_loader import SkillLoader, SkillDefinition, get_skill_loader


FRAUD_SKILL_CONTENT = """\
---
name: fraud-patterns
version: "1.0"
domain: fraud
audience: [agents]
tags: [fraud, risk, detection]
---

# Fraud Patterns

## Beschrijving
Fraude detectie patronen voor VorstersNV.

## Wanneer gebruiken
- Bij nieuwe orders
- Bij hoog bedrag

## Kernkennis

### Risicoscores
Score 75+ blokkeert automatisch.

### Velocity checks
Meer dan 3 orders per uur van hetzelfde IP.
"""

COMMERCE_SKILL_CONTENT = """\
---
name: belgian-commerce
version: "2.0"
domain: commerce
audience: [agents, developers]
tags: [btw, belgie, commerce]
---

# Belgian Commerce

## Wanneer gebruiken
- BTW berekening
- Factuurverwerking
"""

NO_FRONTMATTER_CONTENT = """\
# Bare Skill

## Beschrijving
Een skill zonder frontmatter.

## Wanneer gebruiken
- Altijd
"""


@pytest.fixture
def skills_dir(tmp_path):
    fraud_dir = tmp_path / "fraud-patterns"
    fraud_dir.mkdir()
    (fraud_dir / "SKILL.md").write_text(FRAUD_SKILL_CONTENT, encoding="utf-8")

    commerce_dir = tmp_path / "belgian-commerce"
    commerce_dir.mkdir()
    (commerce_dir / "SKILL.md").write_text(COMMERCE_SKILL_CONTENT, encoding="utf-8")

    return tmp_path


@pytest.fixture
def loader(skills_dir):
    return SkillLoader(skills_dir)


# ── Laden van skills ──────────────────────────────────────────────────────────

def test_loader_loads_both_skills(loader):
    assert len(loader.list_all()) == 2


def test_list_all_contains_fraud(loader):
    assert "fraud-patterns" in loader.list_all()


def test_list_all_contains_commerce(loader):
    assert "belgian-commerce" in loader.list_all()


# ── get() ─────────────────────────────────────────────────────────────────────

def test_get_returns_skill_definition(loader):
    skill = loader.get("fraud-patterns")
    assert isinstance(skill, SkillDefinition)


def test_get_nonexistent_returns_none(loader):
    assert loader.get("does-not-exist") is None


# ── SkillDefinition velden ────────────────────────────────────────────────────

def test_skill_name(loader):
    skill = loader.get("fraud-patterns")
    assert skill.name == "fraud-patterns"


def test_skill_version(loader):
    skill = loader.get("fraud-patterns")
    assert skill.version == "1.0"


def test_skill_domain(loader):
    skill = loader.get("fraud-patterns")
    assert skill.domain == "fraud"


def test_skill_audience_is_list(loader):
    skill = loader.get("fraud-patterns")
    assert isinstance(skill.audience, list)


def test_skill_audience_values(loader):
    skill = loader.get("fraud-patterns")
    assert "agents" in skill.audience


def test_skill_tags_is_list(loader):
    skill = loader.get("fraud-patterns")
    assert isinstance(skill.tags, list)


def test_skill_tags_values(loader):
    skill = loader.get("fraud-patterns")
    assert "fraud" in skill.tags
    assert "risk" in skill.tags
    assert "detection" in skill.tags


def test_skill_folder(loader):
    skill = loader.get("fraud-patterns")
    assert skill.folder == "fraud-patterns"


def test_skill_version_commerce(loader):
    skill = loader.get("belgian-commerce")
    assert skill.version == "2.0"


def test_skill_audience_multiple(loader):
    skill = loader.get("belgian-commerce")
    assert "agents" in skill.audience
    assert "developers" in skill.audience


# ── get_section() ─────────────────────────────────────────────────────────────

def test_get_section_extracts_correct_content(loader):
    skill = loader.get("fraud-patterns")
    section = skill.get_section("Wanneer gebruiken")
    assert section is not None
    assert "Bij nieuwe orders" in section


def test_get_section_nonexistent_returns_none(loader):
    skill = loader.get("fraud-patterns")
    assert skill.get_section("Bestaat niet") is None


def test_get_section_case_insensitive(loader):
    skill = loader.get("fraud-patterns")
    section = skill.get_section("wanneer gebruiken")
    assert section is not None


def test_get_section_stops_at_next_heading(loader):
    skill = loader.get("fraud-patterns")
    section = skill.get_section("Beschrijving")
    assert section is not None
    # Mag niet de inhoud van Wanneer gebruiken bevatten
    assert "Bij nieuwe orders" not in section


def test_get_section_kernkennis_risicoscores(loader):
    skill = loader.get("fraud-patterns")
    # Zoek de subsectie via de bovenliggende ## sectie
    section = skill.get_section("Kernkennis")
    assert section is not None
    assert "Risicoscores" in section
    assert "75+" in section


# ── list_by_domain() ──────────────────────────────────────────────────────────

def test_list_by_domain_fraud(loader):
    results = loader.list_by_domain("fraud")
    assert len(results) == 1
    assert results[0].name == "fraud-patterns"


def test_list_by_domain_commerce(loader):
    results = loader.list_by_domain("commerce")
    assert len(results) == 1
    assert results[0].name == "belgian-commerce"


def test_list_by_domain_empty_for_unknown(loader):
    assert loader.list_by_domain("unknown-domain") == []


# ── list_by_tag() ─────────────────────────────────────────────────────────────

def test_list_by_tag_btw(loader):
    results = loader.list_by_tag("btw")
    assert len(results) == 1
    assert results[0].name == "belgian-commerce"


def test_list_by_tag_fraud(loader):
    results = loader.list_by_tag("fraud")
    assert len(results) == 1
    assert results[0].name == "fraud-patterns"


def test_list_by_tag_empty_for_unknown(loader):
    assert loader.list_by_tag("nonexistent-tag") == []


# ── search() ─────────────────────────────────────────────────────────────────

def test_search_finds_fraud_by_content(loader):
    results = loader.search("risicoscores")
    assert any(s.name == "fraud-patterns" for s in results)


def test_search_finds_by_name(loader):
    results = loader.search("fraud")
    assert any(s.name == "fraud-patterns" for s in results)


def test_search_empty_for_unknown_query(loader):
    assert loader.search("xyz123nonexistent") == []


def test_search_case_insensitive(loader):
    results = loader.search("RISICOSCORES")
    assert any(s.name == "fraud-patterns" for s in results)


def test_search_finds_commerce_by_content(loader):
    results = loader.search("btw berekening")
    assert any(s.name == "belgian-commerce" for s in results)


# ── reload() ──────────────────────────────────────────────────────────────────

def test_reload_still_returns_skills(loader):
    loader.reload()
    assert len(loader.list_all()) == 2


def test_reload_picks_up_new_skill(skills_dir):
    loader = SkillLoader(skills_dir)
    # Laad eerst
    assert len(loader.list_all()) == 2
    # Voeg een derde skill toe
    new_skill_dir = skills_dir / "new-skill"
    new_skill_dir.mkdir()
    (new_skill_dir / "SKILL.md").write_text("""\
---
name: new-skill
version: "1.0"
domain: testing
audience: [developers]
tags: [test]
---

# New Skill

## Beschrijving
Nieuwe skill toegevoegd na initieel laden.
""", encoding="utf-8")
    loader.reload()
    assert "new-skill" in loader.list_all()
    assert len(loader.list_all()) == 3


def test_new_instance_loads_independently(skills_dir):
    loader1 = SkillLoader(skills_dir)
    loader2 = SkillLoader(skills_dir)
    assert loader1.list_all() == loader2.list_all()


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_skills_dir_no_crash(tmp_path):
    loader = SkillLoader(tmp_path)
    assert loader.list_all() == []


def test_nonexistent_dir_no_crash():
    loader = SkillLoader(Path("/nonexistent/path/skills"))
    assert loader.list_all() == []


def test_skill_without_frontmatter_fallback(tmp_path):
    bare_dir = tmp_path / "bare-skill"
    bare_dir.mkdir()
    (bare_dir / "SKILL.md").write_text(NO_FRONTMATTER_CONTENT, encoding="utf-8")
    loader = SkillLoader(tmp_path)
    # Moet geen crash geven; skill geladen met folder-naam als naam
    skills = loader.list_all()
    assert len(skills) == 1
    skill = loader.get(skills[0])
    assert skill is not None
    assert skill.domain == "general"  # fallback domein


def test_skill_without_frontmatter_has_content(tmp_path):
    bare_dir = tmp_path / "bare-skill"
    bare_dir.mkdir()
    (bare_dir / "SKILL.md").write_text(NO_FRONTMATTER_CONTENT, encoding="utf-8")
    loader = SkillLoader(tmp_path)
    skill = loader.get(loader.list_all()[0])
    assert "Bare Skill" in skill.content or "bare-skill" in skill.folder


def test_directory_without_skill_md_is_ignored(skills_dir):
    empty_dir = skills_dir / "no-skill-file"
    empty_dir.mkdir()
    loader = SkillLoader(skills_dir)
    # Enkel de 2 echte skills, de lege map wordt genegeerd
    assert len(loader.list_all()) == 2


def test_non_directory_entries_ignored(skills_dir):
    (skills_dir / "README.md").write_text("# Skills\n", encoding="utf-8")
    loader = SkillLoader(skills_dir)
    assert len(loader.list_all()) == 2


def test_lazy_loading_not_triggered_before_first_call(skills_dir):
    loader = SkillLoader(skills_dir)
    assert not loader._loaded  # nog niet geladen
    loader.list_all()
    assert loader._loaded


def test_get_skill_loader_returns_singleton():
    import ollama.skill_loader as module
    module._loader = None  # reset singleton
    loader1 = get_skill_loader()
    loader2 = get_skill_loader()
    assert loader1 is loader2


def test_skill_content_does_not_include_frontmatter(loader):
    skill = loader.get("fraud-patterns")
    assert "---" not in skill.content.split("\n")[0]
    assert "name: fraud-patterns" not in skill.content
