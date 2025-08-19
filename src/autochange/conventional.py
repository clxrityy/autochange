"""Conventional commit parsing utilities.

Supported syntax (subset):
  type(scope)!: description
  type!: description
  type: description

Breaking changes indicated by trailing ! or a footer line beginning with
"BREAKING CHANGE:" or "BREAKING-CHANGE:".
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Sequence

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?: (?P<description>.+)$"
)

TYPE_MAP: dict[str, str] = {
    "feat": "added",
    "fix": "fixed",
    "perf": "changed",
    "refactor": "changed",
    "docs": "changed",
    "build": "changed",
    "ci": "changed",
    "style": "changed",
    "test": "changed",
    "chore": "changed",
}

BREAKING_FOOTER_RE = re.compile(r"^BREAKING[ -]?CHANGE:\s*(?P<text>.+)$", re.IGNORECASE)

@dataclass
class ParsedCommit:
    raw_type: str
    mapped_type: str | None
    scope: str | None
    description: str
    breaking: bool = False

    def to_change_args(self) -> tuple[str, str, str | None]:
        if not self.mapped_type:
            raise ValueError("Unmappable commit type")
        desc = self.description
        if self.breaking and not desc.lower().startswith("breaking"):
            desc = f"BREAKING: {desc}"
        return self.mapped_type, desc, self.scope

def parse_conventional_commit(message: str) -> ParsedCommit | None:
    lines = message.strip().splitlines()
    if not lines:
        return None
    m = CONVENTIONAL_RE.match(lines[0].strip())
    if not m:
        return None
    raw_type = m.group('type').lower()
    scope = m.group('scope')
    description = m.group('description').strip()
    breaking = bool(m.group('breaking'))
    # footers for breaking change
    if not breaking:
        for line in lines[1:]:
            fm = BREAKING_FOOTER_RE.match(line.strip())
            if fm:
                breaking = True
                footer_text = fm.group('text').strip()
                if footer_text and footer_text.lower() not in description.lower():
                    description = f"{description} ({footer_text})"
                break
    mapped = TYPE_MAP.get(raw_type)
    return ParsedCommit(raw_type, mapped, scope, description, breaking)

def map_commits_to_changes(commits: Sequence[str]) -> list[ParsedCommit]:
    parsed: list[ParsedCommit] = []
    for msg in commits:
        pc = parse_conventional_commit(msg)
        if pc and pc.mapped_type:
            parsed.append(pc)
    return parsed
