from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import List, Optional
import re

CHANGE_TYPES = ["added", "changed", "deprecated", "removed", "fixed", "security"]

@dataclass
class ChangeEntry:
    type: str
    description: str
    scope: Optional[str] = None

    def format(self) -> str:
        scope_part = f"({self.scope}) " if self.scope else ""
        return f"- {scope_part}{self.description}"

@dataclass
class Release:
    version: str
    date: Optional[date] = None
    entries: dict[str, List[ChangeEntry]] = field(default_factory=lambda: {t: [] for t in CHANGE_TYPES})

    def add(self, entry: ChangeEntry):
        if entry.type not in self.entries:
            raise ValueError(f"Unknown change type: {entry.type}")
        self.entries[entry.type].append(entry)

    def is_empty(self) -> bool:
        return all(len(v) == 0 for v in self.entries.values())

    def format(self) -> str:
        d = self.date.isoformat() if self.date else "UNRELEASED"
        lines = [f"## {self.version} - {d}"]
        for t in CHANGE_TYPES:
            if self.entries[t]:
                lines.append(f"### {t.capitalize()}")
                for e in self.entries[t]:
                    lines.append(e.format())
                lines.append("")
        return "\n".join(lines).rstrip() + "\n"

@dataclass
class Changelog:
    releases: List[Release] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> 'Changelog':
        if not path.exists():
            return cls([])
        text = path.read_text(encoding='utf-8')
        return parse_changelog(text)

    def save(self, path: Path):
        path.write_text(self.format(), encoding='utf-8')

    def latest(self) -> Optional[Release]:
        return self.releases[0] if self.releases else None

    def add_unreleased_if_missing(self):
        if not self.releases or self.releases[0].date is not None:
            self.releases.insert(0, Release("Unreleased"))

    def add_change(self, type: str, description: str, scope: Optional[str] = None):
        self.add_unreleased_if_missing()
        entry = ChangeEntry(type=type, description=description, scope=scope)
        self.releases[0].add(entry)

    def release(self, version: str, release_date: Optional[date] = None):
        self.add_unreleased_if_missing()
        unreleased = self.releases[0]
        if unreleased.is_empty():
            raise ValueError("No changes to release")
        unreleased.version = version
        unreleased.date = release_date or date.today()
        # add a fresh unreleased on top
        self.releases.insert(0, Release("Unreleased"))

    def format(self) -> str:
        lines = ["# Changelog", "", "All notable changes to this project will be documented in this file.", ""]
        for rel in self.releases:
            lines.append(rel.format())
        return "\n".join(lines)

CHANGE_HEADER_RE = re.compile(r"^## (?P<version>[^\s]+) - (?P<date>[^\n]+)$")
SECTION_RE = re.compile(r"^### (?P<type>[A-Za-z]+)$")

class _ChangelogParser:
    def __init__(self):
        self.releases: List[Release] = []
        self.current: Release | None = None
        self.current_section: str | None = None

    def feed(self, raw_line: str):
        line = raw_line.strip()
        if not line:
            return
        if line.startswith("## "):
            self._start_release(line)
        elif line.startswith("### "):
            self._start_section(line)
        elif line.startswith("- "):
            self._add_entry(line)

    def _start_release(self, header_line: str):
        m = CHANGE_HEADER_RE.match(header_line)
        if not m:
            return
        version = m.group('version')
        d = m.group('date')
        rel_date = None if d == 'UNRELEASED' else date.fromisoformat(d)
        self.current = Release(version=version, date=rel_date)
        self.releases.append(self.current)
        self.current_section = None

    def _start_section(self, section_line: str):
        if not self.current:
            return
        m = SECTION_RE.match(section_line)
        if not m:
            return
        t = m.group('type').lower()
        self.current_section = t if t in CHANGE_TYPES else None

    def _add_entry(self, entry_line: str):
        if not (self.current and self.current_section):
            return
        desc_line = entry_line[2:].strip()  # trim '- '
        scope = None
        if desc_line.startswith("(") and ") " in desc_line:
            scope, rest = desc_line[1:].split(") ", 1)
            desc_line = rest
        self.current.add(ChangeEntry(type=self.current_section, description=desc_line, scope=scope))

    def finish(self) -> Changelog:
        self.releases.sort(key=lambda r: (r.date or date.max), reverse=True)
        return Changelog(self.releases)


def parse_changelog(text: str) -> Changelog:
    """Parse markdown changelog text into a Changelog model.

    The format expected is similar to Keep a Changelog (subset):
    ## <version> - <date|UNRELEASED>
    ### <Section>
    - (optional-scope) description
    """
    parser = _ChangelogParser()
    for ln in (ln.rstrip() for ln in text.splitlines()):
        parser.feed(ln)
    return parser.finish()
