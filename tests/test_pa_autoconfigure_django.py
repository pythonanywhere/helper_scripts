from unittest.mock import call, patch, Mock
import getpass
import os
from pathlib import Path
import pytest

from scripts.pa_autoconfigure_django import main, download_repo


@pytest.fixture
def mock_main_functions():
    mocks = Mock()
    patchers = []
    functions = [
        'download_repo',
        'DjangoProject',
    ]
    for function in functions:
        mock = getattr(mocks, function)
        patcher = patch(
            'scripts.pa_autoconfigure_django.{}'.format(function),
            mock
        )
        patchers.append(patcher)
        patcher.start()

    yield mocks

    for patcher in patchers:
        patcher.stop()



class TestMain:

    def test_calls_all_stuff_in_right_order(self, mock_main_functions):
        main('https://github.com/pythonanywhere.com/example-django-project.git', 'www.domain.com', 'python.version', nuke='nuke option')
        mock_django_project = mock_main_functions.DjangoProject.return_value
        assert mock_main_functions.method_calls == [
            call.download_repo('https://github.com/pythonanywhere.com/example-django-project.git', 'www.domain.com', nuke='nuke option'),
            call.DjangoProject('www.domain.com'),
        ]
        assert mock_django_project.method_calls == [
            call.sanity_checks(nuke='nuke option'),
            call.create_virtualenv('python.version', 'django', nuke='nuke option'),
            call.update_settings_file(),
            call.run_collectstatic(),
            call.create_webapp(nuke='nuke option'),
            call.update_wsgi_file(),
            call.add_static_file_mappings(),
            call.webapp.reload()
        ]


    def test_domain_defaults_to_using_current_username(self, mock_main_functions):
        username = getpass.getuser()
        main('a-repo', 'your-username.pythonanywhere.com', 'python.version', nuke=False)
        assert mock_main_functions.DjangoProject.call_args == call(
            username + '.pythonanywhere.com'
        )


    def test_lowercases_username(self, mock_main_functions):
        with patch('scripts.pa_autoconfigure_django.getpass') as mock_getpass:
            mock_getpass.getuser.return_value = 'UserName1'
            main('a-url', 'your-username.pythonanywhere.com', 'python.version', 'nukey')
            assert mock_main_functions.DjangoProject.call_args == call(
                'username1.pythonanywhere.com',
            )



class TestDownloadRepo:

    @pytest.mark.slowtest
    def test_actually_downloads_repo(self, fake_home):
        new_folder = download_repo('https://gist.github.com/hjwp/4173bcface139beb7632ec93726f91ea', 'a-domain.com', nuke=False)
        print(os.listdir(fake_home))
        assert new_folder.is_dir()
        assert 'file1.py' in os.listdir(new_folder)
        assert 'file2.py' in os.listdir(new_folder)


    def test_calls_git_subprocess(self, mock_subprocess, fake_home):
        new_folder = download_repo('repo', 'a-domain.com', nuke=False)
        assert new_folder == Path(fake_home) / 'a-domain.com'
        assert mock_subprocess.check_call.call_args == call(
            ['git', 'clone', 'repo', new_folder]
        )


    def test_nuke_option(self, mock_subprocess, fake_home):
        mock_subprocess.check_call.side_effect = lambda *_, **__: Path(fake_home / 'a-domain.com').mkdir()
        Path(fake_home / 'a-domain.com').mkdir()
        Path(fake_home / 'a-domain.com' / 'old-thing.txt').touch()
        new_folder = download_repo('repo', 'a-domain.com', nuke=True)
        assert 'old-thing.txt' not in new_folder.iterdir()

