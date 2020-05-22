import getpass
from unittest.mock import patch

from pythonanywhere.utils import ensure_domain


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
