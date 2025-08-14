from autochange.version import Version

def test_parse_and_str():
    v = Version.parse("1.2.3-alpha+build.5")
    assert str(v) == "1.2.3-alpha+build.5"
    assert v.is_prerelease()

def test_bumps():
    v = Version(1,2,3)
    assert str(v.bump_major()) == "2.0.0"
    assert str(v.bump_minor()) == "1.3.0"
    assert str(v.bump_patch()) == "1.2.4"
