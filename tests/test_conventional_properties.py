from hypothesis import given, strategies as st
import string
from autochange.conventional import parse_conventional_commit, TYPE_MAP

# Build arbitrary conventional-like headers
raw_types = st.sampled_from(list(TYPE_MAP.keys()) + ["unknown", "weird"])

# Restrict scope to safe visible characters to avoid strip() collapsing it to empty.
scope_chars = string.ascii_letters + string.digits + "-_"  # no parenthesis or whitespace
scopes = st.none() | st.text(alphabet=scope_chars, min_size=1, max_size=10)

# Description: printable without control chars or newlines. Allow spaces but require a non-space.
desc_alphabet = string.ascii_letters + string.digits + string.punctuation + " "
descriptions = (
    st.text(alphabet=desc_alphabet, min_size=1, max_size=60)
    .filter(lambda s: any(not c.isspace() for c in s))
)
bang = st.booleans()

@given(raw_types, scopes, descriptions, bang)
def test_parse_round_trip_basic(rtype, scope, desc, bang_flag):
    header = rtype
    if scope:
        header += f"({scope})"
    if bang_flag:
        header += "!"
    header += f": {desc}"
    pc = parse_conventional_commit(header)
    if rtype in TYPE_MAP:
        assert pc is not None
        assert pc.raw_type == rtype
        assert (pc.scope or None) == (scope or None)
        assert pc.description == desc.strip()
        assert pc.breaking == bang_flag
    else:
        # unmapped or invalid types may still parse but have no mapped_type
        if pc:
            assert pc.raw_type == rtype
            # mapped_type is None meaning it will be filtered elsewhere

@given(scopes, descriptions)
def test_breaking_footer_detection(scope, desc):
    # we build a two-line commit with footer
    header = f"feat{f'({scope})' if scope else ''}: {desc}"
    footer_detail = "requires migration"
    msg = header + "\n\nBREAKING CHANGE: " + footer_detail
    pc = parse_conventional_commit(msg)
    assert pc is not None and pc.breaking
    assert footer_detail.split()[0] in pc.description
