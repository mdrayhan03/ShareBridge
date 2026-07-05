from services.account_control import AccountControl


def test_write_then_read(tmp_path):
    p = tmp_path / "account.json"
    ac = AccountControl(str(p))
    ac.write_account("ray", "MD Rayhan Hossain")
    assert ac.read_account() == ("ray", "MD Rayhan Hossain")


def test_missing_returns_none(tmp_path):
    ac = AccountControl(str(tmp_path / "nope.json"))
    assert ac.read_account() == (None, None)


def test_update_overwrites(tmp_path):
    p = tmp_path / "account.json"
    ac = AccountControl(str(p))
    ac.write_account("old", "Old Name")
    ac.update_account("new", "New Name")
    assert ac.read_account() == ("new", "New Name")


def test_explicit_path_does_not_migrate(tmp_path):
    # An explicit filename must never pull in the legacy assets/account.json.
    ac = AccountControl(str(tmp_path / "fresh.json"))
    assert ac.read_account() == (None, None)
