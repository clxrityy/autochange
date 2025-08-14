from __future__ import annotations
import typer
from rich import print
from pathlib import Path
from datetime import date
from .changelog import Changelog, CHANGE_TYPES
from .version import Version
from typing import Optional

app = typer.Typer(help="Manage semantic versions and changelog entries.")

DEFAULT_FILE = Path("CHANGELOG.md")

@app.callback()
def _ensure():
    """Top-level callback reserved for future global options."""

@app.command("init")
def init_cmd(file: Path = typer.Argument(DEFAULT_FILE, help="Target changelog file")):
    if file.exists():
        typer.echo(f"Changelog already exists at {file}")
        raise typer.Exit(code=1)
    cl = Changelog()
    cl.add_unreleased_if_missing()
    cl.save(file)
    print(f"[green]Initialized changelog at {file}[/green]")

@app.command("add")
def add_cmd(
    change_type: str = typer.Option(..., "-t", "--type", case_sensitive=False, help=f"Change type one of: {', '.join(CHANGE_TYPES)}"),
    description: str = typer.Argument(..., help="Change description"),
    scope: Optional[str] = typer.Option(None, "-s", "--scope", help="Optional scope/component"),
    file: Path = typer.Option(DEFAULT_FILE, "-f", "--file", help="Changelog file"),
):
    change_type = change_type.lower()
    if change_type not in CHANGE_TYPES:
        raise typer.BadParameter(f"Type must be one of {CHANGE_TYPES}")
    cl = Changelog.load(file)
    cl.add_change(change_type, description, scope)
    cl.save(file)
    print(f"[cyan]Added {change_type} change:[/cyan] {description}")

@app.command("version")
def version_cmd():
    # derive version from releases (latest released one)
    cl = Changelog.load(DEFAULT_FILE)
    for rel in cl.releases:
        if rel.version.lower() != "unreleased":
            print(rel.version)
            break
    else:
        print("0.0.0")

@app.command("release")
def release_cmd(
    part: str = typer.Argument(..., help="Part to bump: major|minor|patch or explicit version"),
    prerelease: Optional[str] = typer.Option(None, "--prerelease", help="Prerelease tag"),
    file: Path = typer.Option(DEFAULT_FILE, "-f", "--file", help="Changelog file"),
):
    cl = Changelog.load(file)
    # find current version (latest released)
    current = Version(0,0,0)
    for rel in cl.releases:
        if rel.version.lower() != "unreleased":
            current = Version.parse(rel.version)
            break
    # compute next
    if __import__("re").match(r"^\d+\.\d+\.\d+.*", part):
        next_version = Version.parse(part)
    else:
        if part == "major":
            next_version = current.bump_major()
        elif part == "minor":
            next_version = current.bump_minor()
        elif part == "patch":
            next_version = current.bump_patch()
        else:
            raise typer.BadParameter("Unknown part; use major|minor|patch or a full version string")
        if prerelease:
            next_version = next_version.with_prerelease(prerelease)
    cl.release(str(next_version), date.today())
    cl.save(file)
    print(f"[green]Released {next_version}[/green]")

if __name__ == "__main__":
    app()
