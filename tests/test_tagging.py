import subprocess
from pathlib import Path
import textwrap
import os

# Helper to run the installed CLI inside tests
import sys
CLI = [sys.executable, "-m", "autochange.cli"]  # use current interpreter


PROJECT_SRC = Path(__file__).resolve().parents[1] / 'src'

def run(cmd, cwd):
    env = dict(**os.environ)
    existing = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = (str(PROJECT_SRC) + (':' + existing if existing else ''))
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, env=env)
    return result


def init_git_repo(tmp_path: Path):
    subprocess.check_call(["git", "init", "-q"], cwd=tmp_path)
    subprocess.check_call(["git", "config", "user.name", "Test User"], cwd=tmp_path)
    subprocess.check_call(["git", "config", "user.email", "test@example.com"], cwd=tmp_path)
    # initial commit
    (tmp_path / "README.md").write_text("init\n", encoding="utf-8")
    subprocess.check_call(["git", "add", "README.md"], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-m", "chore: initial"], cwd=tmp_path)


def test_tag_command_creates_tag_for_existing_release(tmp_path):
    init_git_repo(tmp_path)
    changelog = textwrap.dedent(
        """# Changelog

        ## 0.1.0 - 2025-08-18
        ### Added
        - Initial feature
        """
    ).strip() + "\n"
    (tmp_path / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    subprocess.check_call(["git", "add", "CHANGELOG.md"], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-m", "docs: add changelog"], cwd=tmp_path)

    result = run(CLI + ["tag", "0.1.0"], tmp_path)
    assert result.returncode == 0, result.stderr
    tags = subprocess.check_output(["git", "tag"], cwd=tmp_path, text=True).split()
    assert "v0.1.0" in tags
    message = subprocess.check_output(["git", "show", "-s", "--format=%B", "v0.1.0"], cwd=tmp_path, text=True)
    # Tag message should contain release version or entries; ensure version appears somewhere
    assert "0.1.0" in message


def test_release_with_tag_and_commit_creates_tag(tmp_path):
    init_git_repo(tmp_path)
    # init changelog
    result = run(CLI + ["init"], tmp_path)
    assert result.returncode == 0, result.stderr
    # add change
    result = run(CLI + ["add", "-t", "added", "New feature"], tmp_path)
    assert result.returncode == 0, result.stderr
    # release with tagging
    result = run(CLI + ["release", "patch", "--tag", "--commit"], tmp_path)
    assert result.returncode == 0, result.stderr
    tags = subprocess.check_output(["git", "tag"], cwd=tmp_path, text=True).split()
    assert "v0.0.1" in tags
    message = subprocess.check_output(["git", "show", "-s", "--format=%B", "v0.0.1"], cwd=tmp_path, text=True)
    assert "0.0.1" in message
