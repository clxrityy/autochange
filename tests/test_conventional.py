from autochange.conventional import (
    parse_conventional_commit,
    map_commits_to_changes,
)


def test_parse_basic_feat():
    msg = "feat: add login"
    pc = parse_conventional_commit(msg)
    assert pc is not None
    assert pc.raw_type == "feat"
    assert pc.mapped_type == "added"
    assert pc.description == "add login"
    assert not pc.breaking


def test_parse_with_scope_and_breaking_bang():
    msg = "feat(auth)!: introduce oauth2"
    pc = parse_conventional_commit(msg)
    assert pc is not None and pc.breaking
    t, desc, scope = pc.to_change_args()
    assert t == "added"
    assert scope == "auth"
    assert desc.startswith("BREAKING:")


def test_parse_breaking_footer():
    msg = "fix(db): adjust pool size\n\nBREAKING CHANGE: requires reconfig"
    pc = parse_conventional_commit(msg)
    assert pc is not None and pc.breaking
    assert "requires reconfig" in pc.description


def test_unmapped_type_filtered():
    msgs = ["unknown: something", "feat: x"]
    parsed = map_commits_to_changes(msgs)
    # only feat should be included
    assert len(parsed) == 1
    assert parsed[0].raw_type == "feat"


def test_map_multiple():
    msgs = [
        "feat(parser): add new grammar",
        "fix: null ref",
        "refactor(core): cleanup",
    ]
    parsed = map_commits_to_changes(msgs)
    kinds = {p.mapped_type for p in parsed}
    assert {"added", "fixed", "changed"}.issubset(kinds)
