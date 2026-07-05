from services.update_checker import is_newer, parse_release


def test_is_newer_basic():
    assert is_newer("2.0.0", "1.0.0")
    assert is_newer("v2.0.0", "1.0.0")        # leading v tolerated
    assert is_newer("1.10.0", "1.9.0")        # numeric, not string, compare
    assert not is_newer("1.0.0", "1.0.0")     # equal
    assert not is_newer("1.0.0", "2.0.0")     # older
    assert not is_newer("garbage", "1.0.0")   # unparseable -> not newer


def test_is_newer_uneven_lengths():
    assert is_newer("1.2", "1.1.9")
    assert not is_newer("1.2", "1.2.0")


def test_parse_release_newer():
    payload = {
        "tag_name": "v2.0.0",
        "html_url": "https://github.com/mdrayhan03/ShareBridge/releases/tag/v2.0.0",
        "body": "  New host migration!  ",
    }
    info = parse_release(payload, "1.0.0")
    assert info is not None
    assert info["version"] == "v2.0.0"
    assert info["url"].endswith("v2.0.0")
    assert info["notes"] == "New host migration!"


def test_parse_release_same_or_older_returns_none():
    assert parse_release({"tag_name": "1.0.0"}, "1.0.0") is None
    assert parse_release({"tag_name": "v0.9.0"}, "1.0.0") is None


def test_parse_release_bad_payload():
    assert parse_release(None, "1.0.0") is None
    assert parse_release({}, "1.0.0") is None
    assert parse_release({"tag_name": ""}, "1.0.0") is None
