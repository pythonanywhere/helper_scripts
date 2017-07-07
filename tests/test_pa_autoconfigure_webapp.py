from unittest.mock import call, patch, Mock
import getpass
import pytest

from scripts.pa_autoconfigure_webapp import main


@pytest.fixture
def mock_main_functions():
    mocks = Mock()
    patchers = []
    functions = [
        'sanity_checks',
        'download_repo',
        'create_virtualenv',
        # 'create_webapp',
        # 'run_collectstatic',
        # 'add_static_file_mappings',
        # 'update_wsgi_file',
        # 'reload_webapp',
    ]
    for function in functions:
        mock = getattr(mocks, function)
        patcher = patch(
            'scripts.pa_autoconfigure_webapp.{}'.format(function),
            mock
        )
        patchers.append(patcher)
        patcher.start()

    yield mocks

    for patcher in patchers:
        patcher.stop()



class TestMain:

    def test_sanity_checks_then_downloads_repo_and_finds_virtualenv(self, mock_main_functions):
        main('https://github.com/pythonanywhere.com/example-django-project.git', 'www.domain.com', 'python.version', nuke='nuke option')
        assert mock_main_functions.method_calls[:3] == [
            call.sanity_checks('www.domain.com', nuke='nuke option'),
            call.download_repo('https://github.com/pythonanywhere.com/example-django-project.git'),
            call.create_virtualenv(
                'www.domain.com', 'python.version', 'django.version', nuke='nuke option'
            ),
        ]

    def test_domain_defaults_to_using_current_username(self, mock_main_functions):
        username = getpass.getuser()
        main('a-repo', 'your-username.pythonanywhere.com', 'python.version', nuke=False)
        assert mock_main_functions.sanity_checks.call_args == call(
            username + '.pythonanywhere.com', nuke=False
        )


    def test_lowercases_username(self, mock_main_functions):
        with patch('scripts.pa_autoconfigure_webapp.getpass') as mock_getpass:
            mock_getpass.getuser.return_value = 'UserName1'
            main('your-username.pythonanywhere.com', 'django.version', 'python.version', 'nukey')
            assert mock_main_functions.sanity_checks.call_args == call(
                'username1.pythonanywhere.com', nuke='nukey'
            )

