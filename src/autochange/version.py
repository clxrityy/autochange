from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Optional

SEMVER_RE = re.compile(r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>[0-9A-Za-z-\.]+))?(?:\+(?P<buildmeta>[0-9A-Za-z-\.]+))?$")

@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    buildmeta: Optional[str] = None

    def __post_init__(self):
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError("Version numbers must be non-negative")
        if self.prerelease and not re.match(r"^[0-9A-Za-z-\.]+$", self.prerelease):
            raise ValueError("Invalid prerelease segment")
        if self.buildmeta and not re.match(r"^[0-9A-Za-z-\.]+$", self.buildmeta):
            raise ValueError("Invalid build metadata segment")

    @classmethod
    def parse(cls, text: str) -> "Version":
        m = SEMVER_RE.match(text.strip())
        if not m:
            raise ValueError(f"Not a valid semantic version: {text}")
        parts = m.groupdict()
        return cls(int(parts['major']), int(parts['minor']), int(parts['patch']), parts['prerelease'], parts['buildmeta'])

    def bump_major(self, prerelease: Optional[str] = None) -> "Version":
        return Version(self.major + 1, 0, 0, prerelease)

    def bump_minor(self, prerelease: Optional[str] = None) -> "Version":
        return Version(self.major, self.minor + 1, 0, prerelease)

    def bump_patch(self, prerelease: Optional[str] = None) -> "Version":
        return Version(self.major, self.minor, self.patch + 1, prerelease)

    def with_prerelease(self, tag: Optional[str]) -> "Version":
        return Version(self.major, self.minor, self.patch, tag, self.buildmeta)

    def with_build(self, meta: Optional[str]) -> "Version":
        return Version(self.major, self.minor, self.patch, self.prerelease, meta)

    def is_prerelease(self) -> bool:
        return self.prerelease is not None

    def __str__(self) -> str:  # canonical form
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        if self.buildmeta:
            base += f"+{self.buildmeta}"
        return base
