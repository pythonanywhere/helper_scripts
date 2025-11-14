import getpass
from unittest.mock import patch

import pytest

from pythonanywhere.utils import ensure_domain, format_log_deletion_message


class TestEnsureDomain:
    def test_domain_defaults_to_using_current_username_and_domain_from_env(
        self, monkeypatch
    ):
        username = getpass.getuser()
        monkeypatch.setenv("PYTHONANYWHERE_DOMAIN", "pythonanywhere.domain")

        result = ensure_domain("your-username.pythonanywhere.com")

        assert result == f"{username}.pythonanywhere.domain"

    def test_lowercases_username(self, monkeypatch):
        with patch('pythonanywhere.utils.getpass') as mock_getpass:
            mock_getpass.getuser.return_value = 'UserName1'

            result = ensure_domain("your-username.pythonanywhere.com")

        assert result == 'username1.pythonanywhere.com'

    def test_custom_domain_remains_unchanged(self):
        custom_domain = "foo.bar.baz"

        result = ensure_domain(custom_domain)

        assert result == custom_domain


@pytest.mark.parametrize(
    "domain,log_type,log_index,expected",
    [
        ("foo.com", "access", 0, "Deleting current access log file for foo.com via API"),
        ("bar.com", "error", 2, "Deleting old (archive number 2) error log file for bar.com via API"),
        ("baz.com", "server", 9, "Deleting old (archive number 9) server log file for baz.com via API"),
    ],
)
def test_format_log_deletion_message_with_various_inputs(domain, log_type, log_index, expected):
    result = format_log_deletion_message(domain, log_type, log_index)

    assert result == expected
