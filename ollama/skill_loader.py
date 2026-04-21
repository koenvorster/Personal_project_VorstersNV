from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SkillDefinition:
    name: str
    version: str
    domain: str
    audience: list[str]
    tags: list[str]
    content: str          # volledig markdown na frontmatter
    folder: str           # naam van de folder

    def get_section(self, section_name: str) -> Optional[str]:
        """Extracts a ## Section from content."""
        lines = self.content.split('\n')
        in_section = False
        section_lines = []
        for line in lines:
            if line.startswith('## ') and section_name.lower() in line.lower():
                in_section = True
                continue
            elif line.startswith('## ') and in_section:
                break
            elif in_section:
                section_lines.append(line)
        return '\n'.join(section_lines).strip() if section_lines else None


class SkillLoader:
    SKILLS_DIR = Path(__file__).parent.parent / ".claude" / "skills"

    def __init__(self, skills_dir: Optional[Path] = None):
        self._dir = skills_dir or self.SKILLS_DIR
        self._skills: dict[str, SkillDefinition] = {}
        self._loaded = False

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parses YAML frontmatter between --- markers."""
        if not content.startswith('---'):
            return {}, content
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content
        try:
            import yaml
            meta = yaml.safe_load(parts[1]) or {}
        except Exception:
            meta = {}
        return meta, parts[2].strip()

    def _ensure_loaded(self):
        if not self._loaded:
            self._load_all()
            self._loaded = True

    def _load_all(self):
        if not self._dir.exists():
            return
        for skill_dir in self._dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            try:
                raw = skill_file.read_text(encoding='utf-8')
                meta, body = self._parse_frontmatter(raw)
                skill = SkillDefinition(
                    name=meta.get('name', skill_dir.name),
                    version=str(meta.get('version', '1.0')),
                    domain=meta.get('domain', 'general'),
                    audience=meta.get('audience', []),
                    tags=meta.get('tags', []),
                    content=body,
                    folder=skill_dir.name,
                )
                self._skills[skill.name] = skill
            except Exception:
                pass

    def reload(self):
        """Wist de cache en herlaadt alle skills."""
        self._skills = {}
        self._loaded = False
        self._ensure_loaded()

    def get(self, name: str) -> Optional[SkillDefinition]:
        self._ensure_loaded()
        return self._skills.get(name)

    def list_all(self) -> list[str]:
        self._ensure_loaded()
        return list(self._skills.keys())

    def list_by_domain(self, domain: str) -> list[SkillDefinition]:
        self._ensure_loaded()
        return [s for s in self._skills.values() if s.domain == domain]

    def list_by_tag(self, tag: str) -> list[SkillDefinition]:
        self._ensure_loaded()
        return [s for s in self._skills.values() if tag in s.tags]

    def search(self, query: str) -> list[SkillDefinition]:
        """Simple text search in skill content."""
        self._ensure_loaded()
        q = query.lower()
        return [s for s in self._skills.values() if q in s.content.lower() or q in s.name.lower()]


def get_skill_loader() -> "SkillLoader":
    global _loader
    if _loader is None:
        _loader = SkillLoader()
    return _loader


_loader: Optional[SkillLoader] = None
