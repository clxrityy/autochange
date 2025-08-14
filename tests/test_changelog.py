from pathlib import Path
from autochange.changelog import Changelog, parse_changelog
from datetime import date

def test_add_and_release(tmp_path: Path):
    file = tmp_path / "CHANGELOG.md"
    cl = Changelog()
    cl.add_change("added", "New feature", scope="api")
    cl.add_change("fixed", "Bug fix")
    cl.release("0.1.0", date(2025,8,13))
    cl.save(file)
    text = file.read_text()
    assert "0.1.0" in text
    assert "New feature" in text
    assert "Bug fix" in text


def test_parse():
    sample = """# Changelog\n\n## 0.1.0 - 2025-08-13\n### Added\n- (api) New feature\n\n### Fixed\n- Bug fix\n"""
    cl = parse_changelog(sample)
    assert cl.releases
    assert any(r.version == '0.1.0' for r in cl.releases)
