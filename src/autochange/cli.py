from __future__ import annotations
import typer
from rich import print
from pathlib import Path
from datetime import date
from .changelog import Changelog, CHANGE_TYPES
from .conventional import map_commits_to_changes
import subprocess
from .version import Version
from typing import Optional
import re

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
    part: str = typer.Argument(..., help="Part to bump: major|minor|patch|auto or explicit version"),
    prerelease: Optional[str] = typer.Option(None, "--prerelease", help="Prerelease tag"),
    file: Path = typer.Option(DEFAULT_FILE, "-f", "--file", help="Changelog file"),
    tag: bool = typer.Option(False, "--tag", help="Create a git tag for the release after updating changelog"),
    push: bool = typer.Option(False, "--push", help="Push tag to origin (implies --tag)"),
    sign: bool = typer.Option(False, "--sign", help="Sign the tag with GPG (implies --tag)"),
    force_tag: bool = typer.Option(False, "--force-tag", help="Overwrite existing tag if present"),
    dirty_ok: bool = typer.Option(False, "--dirty-ok", help="Allow creating tag on a dirty working tree"),
    commit: bool = typer.Option(False, "--commit", help="Create a release commit before tagging"),
):
    cl = Changelog.load(file)
    current_str = _latest_released_version_from_changelog(cl)
    current = Version.parse(current_str) if current_str else Version(0, 0, 0)
    next_version = _compute_target_version(part, prerelease, current, file)
    cl.release(str(next_version), date.today())
    cl.save(file)
    _update_pyproject_version(str(next_version))
    print(f"[green]Released {next_version}[/green]")
    _maybe_tag_release(next_version, file=file, tag=tag, push=push, sign=sign,
                       force_tag=force_tag, dirty_ok=dirty_ok, commit=commit)

def _compute_target_version(part: str, prerelease: Optional[str], current: Version, file: Path) -> Version:
    import re
    if part == "auto":
        inferred = _infer_bump(Changelog.load(file))
        print(f"[cyan]Auto-detected bump: {inferred}[/cyan]")
        part_to_use = inferred
    else:
        part_to_use = part
    if re.match(r"^\d+\.\d+\.\d+.*", part_to_use):
        return Version.parse(part_to_use)
    bump_map = {
        "major": current.bump_major,
        "minor": current.bump_minor,
        "patch": current.bump_patch,
    }
    if part_to_use not in bump_map:
        raise typer.BadParameter("Unknown part; use major|minor|patch|auto or a full version string")
    version = bump_map[part_to_use]()
    if prerelease:
        version = version.with_prerelease(prerelease)
    return version

def _maybe_tag_release(next_version: Version, *, file: Path, tag: bool, push: bool,
                       sign: bool, force_tag: bool, dirty_ok: bool, commit: bool):
    if push or sign:
        tag = True
    if not tag:
        return
    if commit:
        _commit_release(file, str(next_version))
    _create_tag(str(next_version), file=file, push=push, force=force_tag, sign=sign, dirty_ok=dirty_ok)

def _resolve_since(since: Optional[str]) -> Optional[str]:
    if since is not None:
        return since
    try:
        return subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], text=True).strip()
    except subprocess.CalledProcessError:
        return None

def _git_log(rev_range: str) -> str:
    log_format = "%H%n%s%n%b%n==END=="
    try:
        return subprocess.check_output(
            ["git", "log", "--no-color", "--pretty=format:" + log_format, rev_range],
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise typer.Exit(code=1) from e

def _parse_git_messages(raw: str) -> list[str]:
    messages: list[str] = []
    current: list[str] = []
    for line in raw.splitlines():
        if line == "==END==":
            if current:
                messages.append("\n".join(current).strip())
                current = []
        else:
            current.append(line)
    return messages

def _print_dry_run(commits):
    for c in commits:
        print(f"{c.raw_type}{'!' if c.breaking else ''}{'(' + c.scope + ')' if c.scope else ''}: -> {c.mapped_type} | {c.description}")

def _apply_commits_to_changelog(commits, file: Path):
    cl = Changelog.load(file)
    for c in commits:
        t, desc, scope = c.to_change_args()
        cl.add_change(t, desc, scope)
    cl.save(file)
    print(f"[green]Imported {len(commits)} commits into changelog.[/green]")

@app.command("import-commits")
def import_commits(
    since: str = typer.Option(None, "--since", help="Git ref (tag/sha) to start from (exclusive). If omitted, last tag is used."),
    until: str = typer.Option("HEAD", "--until", help="Git ref to end at (inclusive)."),
    file: Path = typer.Option(DEFAULT_FILE, "-f", "--file", help="Changelog file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be added without modifying the file."),
):
    """Parse conventional commits in a git range and add them to the unreleased section."""
    since = _resolve_since(since)
    rev_range = f"{since}..{until}" if since else until
    raw = _git_log(rev_range)
    commits = map_commits_to_changes(_parse_git_messages(raw))
    if not commits:
        print("[yellow]No conventional commits found in range.[/yellow]")
        raise typer.Exit()
    if dry_run:
        _print_dry_run(commits)
        raise typer.Exit()
    _apply_commits_to_changelog(commits, file)

def _working_tree_clean() -> bool:
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], text=True)
        return out.strip() == ""
    except Exception:
        return True  # if git not available, treat as clean to fail later gracefully

def _commit_release(file: Path, version: str):
    try:
        subprocess.check_call(["git", "add", str(file)])
        pyproject = Path("pyproject.toml")
        if pyproject.exists():
            subprocess.check_call(["git", "add", str(pyproject)])
        subprocess.check_call(["git", "commit", "-m", f"chore(release): v{version}"])
        print(f"[green]Committed release v{version}[/green]")
    except subprocess.CalledProcessError as e:
        print(f"[red]Failed to commit release: {e}[/red]")
        raise typer.Exit(code=1)

def _latest_released_version_from_changelog(cl: Changelog) -> Optional[str]:
    for rel in cl.releases:
        if rel.version.lower() != "unreleased":
            return rel.version
    return None

def _normalize_tag(version: str) -> str:
    return version if version.startswith('v') else f'v{version}'

def _infer_bump(cl: Changelog) -> str:
    cl.add_unreleased_if_missing()
    unreleased = cl.releases[0]
    if unreleased.version.lower() != 'unreleased':
        raise typer.BadParameter("No unreleased changes to infer from")
    has_any = False
    breaking = False
    for entries in unreleased.entries.values():
        if entries:
            has_any = True
            if any('breaking' in e.description.lower() for e in entries):
                breaking = True
                break
    if not has_any:
        raise typer.BadParameter("No unreleased changes to infer bump")
    if breaking:
        return 'major'
    if unreleased.entries.get('added'):
        return 'minor'
    return 'patch'

def _safe_read_file(path: Path) -> Optional[str]:
    try:
        return path.read_text()
    except Exception:
        return None

def _find_project_bounds(lines: list[str]) -> tuple[Optional[int], Optional[int]]:
    for i, line in enumerate(lines):
        if line.strip() == "[project]":
            j = i + 1
            while j < len(lines):
                stripped = lines[j].lstrip()
                if stripped.startswith("[") and stripped.rstrip().endswith("]"):
                    break
                j += 1
            return i, j
    return None, None

def _ensure_version_line(lines: list[str], new_version: str, start: int, end: int) -> bool:
    version_pattern = re.compile(r'^\s*version\s*=')
    value_pattern = re.compile(r'^(\s*)version\s*=\s*["\']([^"\']+)["\']')
    for k in range(start + 1, end):
        if version_pattern.match(lines[k]):
            m = value_pattern.match(lines[k])
            if m and m.group(2) == new_version:
                return False  # already correct
            indent = m.group(1) if m else re.match(r'^(\s*)', lines[k]).group(1)
            original = lines[k]
            lines[k] = f'{indent}version = "{new_version}"\n'
            return lines[k] != original
    # No version line found inside section; insert one
    lines.insert(end, f'version = "{new_version}"\n')
    return True

def _safe_write_file(path: Path, text: str, new_version: str):
    try:
        path.write_text(text)
        print(f"[green]Updated pyproject.toml version to {new_version}[/green]")
    except Exception:
        pass

def _update_pyproject_version(new_version: str, path: Path = Path("pyproject.toml")):
    """Update version inside [project] section; noop if file/section missing."""
    if not path.exists():
        return
    text = _safe_read_file(path)
    if text is None:
        return
    lines = text.splitlines(keepends=True)
    start, end = _find_project_bounds(lines)
    if start is None:
        return
    changed = _ensure_version_line(lines, new_version, start, end)
    if not changed:
        return
    new_text = ''.join(lines)
    if new_text == text:
        return
    _safe_write_file(path, new_text, new_version)

def _get_tag_name_and_release(version: str, file: Path) -> tuple[str, str, str]:
    cl = Changelog.load(file)
    resolved_version = version or _latest_released_version_from_changelog(cl)
    if not resolved_version:
        print("[red]No released version found to tag.[/red]")
        raise typer.Exit(code=1)
    tag_name = _normalize_tag(resolved_version)
    rel = next((r for r in cl.releases if r.version == resolved_version), None)
    message = f"Release {resolved_version}" if not rel else rel.format().strip()
    return tag_name, resolved_version, message

def _check_existing_tag(tag_name: str) -> bool:
    try:
        existing = subprocess.check_output(["git", "tag", "--list", tag_name], text=True).strip()
    except FileNotFoundError:
        print("[red]Git not available in PATH.[/red]")
        raise typer.Exit(code=1)
    except subprocess.CalledProcessError:
        existing = ""
    return bool(existing)

def _delete_tag(tag_name: str):
    try:
        subprocess.check_call(["git", "tag", "-d", tag_name])
    except subprocess.CalledProcessError as e:
        print(f"[red]Failed to delete existing tag {tag_name}: {e}[/red]")
        raise typer.Exit(code=1)

def _build_tag_cmd(tag_name: str, message: str, sign: bool) -> list[str]:
    cmd = ["git", "tag", "-s" if sign else "-a", tag_name, "-m", message]
    return cmd

def _create_tag(version: str, *, file: Path, push: bool, force: bool, sign: bool, dirty_ok: bool):
    if not dirty_ok and not _working_tree_clean():
        print("[red]Working tree is dirty. Commit or stash changes, or use --dirty-ok.[/red]")
        raise typer.Exit(code=1)
    tag_name, _, message = _get_tag_name_and_release(version, file)
    existing = _check_existing_tag(tag_name)
    if existing and not force:
        print(f"[yellow]Tag {tag_name} already exists (use --force-tag or --force when using tag command).[/yellow]")
        raise typer.Exit(code=1)
    if existing and force:
        _delete_tag(tag_name)
    cmd = _build_tag_cmd(tag_name, message, sign)
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"[red]Failed to create tag: {e}[/red]")
        raise typer.Exit(code=1)
    print(f"[green]Created tag {tag_name}[/green]")
    if push:
        try:
            subprocess.check_call(["git", "push", "origin", tag_name])
            print(f"[green]Pushed tag {tag_name} to origin[/green]")
        except subprocess.CalledProcessError as e:
            print(f"[red]Failed to push tag: {e}[/red]")
            raise typer.Exit(code=1)

@app.command("tag")
def tag_cmd(
    version: Optional[str] = typer.Argument(None, help="Version to tag (defaults to latest released in changelog)"),
    file: Path = typer.Option(DEFAULT_FILE, "-f", "--file", help="Changelog file"),
    push: bool = typer.Option(False, "--push", help="Push tag to origin after creation"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing tag if it exists"),
    sign: bool = typer.Option(False, "--sign", help="Sign tag with GPG"),
    dirty_ok: bool = typer.Option(False, "--dirty-ok", help="Allow creating tag on dirty working tree"),
):
    """Create a git tag for a released version (stand-alone)."""
    _create_tag(version or "", file=file, push=push, force=force, sign=sign, dirty_ok=dirty_ok)

if __name__ == "__main__":  # pragma: no cover
    app()
