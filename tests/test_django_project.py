from unittest.mock import call, patch, Mock
from pathlib import Path
import os
import tempfile
from textwrap import dedent
import pytest
import shutil
import subprocess

import pythonanywhere.django_project
from pythonanywhere.django_project import DjangoProject
from pythonanywhere.exceptions import SanityException



class TestDownloadRepo:

    @pytest.mark.slowtest
    def test_actually_downloads_repo(self, fake_home):
        repo = 'https://gist.github.com/hjwp/4173bcface139beb7632ec93726f91ea'
        project = DjangoProject('www.a.domain.com', 'py.version')
        project.download_repo(repo, nuke=False)
        assert project.project_path.is_dir()
        assert 'file1.py' in os.listdir(project.project_path)
        assert 'file2.py' in os.listdir(project.project_path)


    def test_calls_git_subprocess(self, mock_subprocess, fake_home):
        project = DjangoProject('www.a.domain.com', 'py.version')
        project.download_repo('repo', nuke=False)
        assert mock_subprocess.check_call.call_args == call(
            ['git', 'clone', 'repo', project.project_path]
        )


    def test_nuke_option_deletes_directory_first(self, mock_subprocess, fake_home):
        project = DjangoProject('www.a.domain.com', 'py.version')
        project.project_path.mkdir()
        (project.project_path / 'old-thing.txt').touch()
        mock_subprocess.check_call.side_effect = lambda *_, **__: Path(project.project_path).mkdir()

        project.download_repo('repo', nuke=True)
        assert 'old-thing.txt' not in project.project_path.iterdir()


    def test_nuke_option_ignores_directory_doesnt_exist(self, mock_subprocess, fake_home):
        project = DjangoProject('www.a.domain.com', 'py.version')
        mock_subprocess.check_call.side_effect = lambda *_, **__: Path(project.project_path).mkdir()

        project.download_repo('repo', nuke=True)  # should not raise

        assert project.project_path.is_dir()


class TestDetectDjangoVersion:

    def test_is_django_by_default(self, fake_home):
        project = DjangoProject('mydomain.com', 'python.version')
        assert project.detect_django_version() == 'django'


    def test_if_requirements_txt_exists(self, fake_home):
        project = DjangoProject('mydomain.com', 'python.version')
        project.project_path.mkdir()
        requirements_txt = project.project_path / 'requirements.txt'
        requirements_txt.touch()
        assert project.detect_django_version() == f'-r {requirements_txt.resolve()}'



class TestCreateVirtualenv:

    def test_calls_create_virtualenv(self):
        project = DjangoProject('mydomain.com', 'python.version')
        with patch('pythonanywhere.django_project.create_virtualenv') as mock_create_virtualenv:
            project.create_virtualenv('django.version', nuke='nuke option')
        assert mock_create_virtualenv.call_args == call(
            project.domain, project.python_version, 'django==django.version', nuke='nuke option'
        )


    def test_special_cases_latest_django_version(self):
        project = DjangoProject('mydomain.com', 'python.version')
        with patch('pythonanywhere.django_project.create_virtualenv') as mock_create_virtualenv:
            project.create_virtualenv(django_version='latest', nuke='nuke option')
        assert mock_create_virtualenv.call_args == call(
            project.domain, project.python_version, 'django', nuke='nuke option'
        )


    def test_uses_detect_if_django_version_not_specified(self):
        project = DjangoProject('mydomain.com', 'python.version')
        project.detect_django_version = Mock()
        with patch('pythonanywhere.django_project.create_virtualenv') as mock_create_virtualenv:
            project.create_virtualenv(nuke='nuke option')
        assert mock_create_virtualenv.call_args == call(
            project.domain, project.python_version, project.detect_django_version.return_value, nuke='nuke option'
        )


    def test_sets_virtualenv_attribute(self):
        project = DjangoProject('mydomain.com', 'python.version')
        with patch('pythonanywhere.django_project.create_virtualenv') as mock_create_virtualenv:
            project.create_virtualenv(django_version='django.version', nuke='nuke option')
        assert project.virtualenv_path == mock_create_virtualenv.return_value




class TestRunStartproject:

    def test_creates_folder(self, mock_subprocess, fake_home):
        project = DjangoProject('mydomain.com', 'python.version')
        project.virtualenv_path = '/path/to/virtualenv'
        project.run_startproject(nuke=False)
        assert (fake_home / 'mydomain.com').is_dir()


    def test_calls_startproject(self, mock_subprocess, fake_home):
        project = DjangoProject('mydomain.com', 'python.version')
        project.virtualenv_path = '/path/to/virtualenv'
        project.run_startproject(nuke=False)
        assert mock_subprocess.check_call.call_args == call([
            Path('/path/to/virtualenv/bin/django-admin.py'),
            'startproject',
            'mysite',
            fake_home / 'mydomain.com',
        ])


    def test_nuke_option_deletes_directory_first(self, mock_subprocess, fake_home):
        project = DjangoProject('mydomain.com', 'python.version')
        project.virtualenv_path = '/path/to/virtualenv'
        (fake_home / project.domain).mkdir()
        old_file = fake_home / project.domain / 'old_file.py'
        old_file.write_text('old stuff')

        project.run_startproject(nuke=True)

        assert not old_file.exists()


    def test_nuke_option_handles_directory_not_existing(self, mock_subprocess, fake_home):
        project = DjangoProject('mydomain.com', 'python.version')
        project.virtualenv_path = '/path/to/virtualenv'
        project.run_startproject(nuke=True)  # should not raise



@pytest.fixture
def non_nested_submodule():
    subprocess.check_call(['git', 'submodule', 'update', '--init', '--recursive'])
    submodule_path = Path(__file__).parents[1] / 'submodules' / 'example-django-project'
    subprocess.check_call(
        ['git', 'checkout', 'master'],
        cwd=submodule_path
    )
    yield submodule_path
    subprocess.check_call(['git', 'submodule', 'update', '--init', '--recursive'])


@pytest.fixture
def more_nested_submodule():
    subprocess.check_call(['git', 'submodule', 'update', '--init', '--recursive'])
    submodule_path = Path(__file__).parents[1] / 'submodules' / 'example-django-project'
    subprocess.check_call(
        ['git', 'checkout', 'morenested'],
        cwd=submodule_path
    )
    yield submodule_path
    subprocess.check_call(['git', 'submodule', 'update', '--init', '--recursive'])



class TestFindDjangoFiles:

    def test_non_nested(self, fake_home, non_nested_submodule):

        project = DjangoProject('mydomain.com', 'python.version')
        shutil.copytree(non_nested_submodule, project.project_path)
        expected_settings_path = project.project_path / 'myproject/settings.py'
        assert expected_settings_path.exists()
        expected_manage_py = project.project_path / 'manage.py'
        assert expected_manage_py.exists()

        project.find_django_files()

        assert project.settings_path == expected_settings_path
        assert project.manage_py_path == expected_manage_py


    def test_nested(self, fake_home, more_nested_submodule):
        project = DjangoProject('mydomain.com', 'python.version')
        shutil.copytree(more_nested_submodule, project.project_path)
        expected_settings_path = project.project_path / 'mysite/mysite/settings.py'
        assert expected_settings_path.exists()
        expected_manage_py = project.project_path / 'mysite/manage.py'
        assert expected_manage_py.exists()

        project.find_django_files()

        assert project.settings_path == expected_settings_path
        assert project.manage_py_path == expected_manage_py


    def test_raises_if_empty_project_folder(self, fake_home):
        project = DjangoProject('mydomain.com', 'python.version')
        with pytest.raises(SanityException) as e:
            project.find_django_files()

        assert 'Could not find your settings.py' in str(e.value)


    def test_raises_if_no_settings_in_any_subfolders(self, fake_home):
        project = DjangoProject('mydomain.com', 'python.version')
        not_this_folder = project.project_path / 'not_this_folder'
        not_this_folder.mkdir(parents=True)
        with pytest.raises(SanityException) as e:
            project.find_django_files()

        assert 'Could not find your settings.py' in str(e.value)


    def test_raises_if_manage_py_not_found(self, fake_home, non_nested_submodule):
        project = DjangoProject('mydomain.com', 'python.version')
        shutil.copytree(non_nested_submodule, project.project_path)
        expected_manage_py = project.project_path / 'manage.py'
        assert expected_manage_py.exists()
        expected_manage_py.unlink()
        with pytest.raises(SanityException) as e:
            project.find_django_files()

        assert 'Could not find your manage.py' in str(e.value)



class TestUpdateSettingsFile:

    def test_adds_STATIC_and_MEDIA_config_to_settings(self):
        project = DjangoProject('mydomain.com', 'python.version')
        project.settings_path = Path(tempfile.NamedTemporaryFile().name)

        with open(project.settings_path, 'w') as f:
            f.write(dedent(
                """
                # settings file
                STATIC_URL = '/static/'
                ALLOWED_HOSTS = []
                """
            ))

        project.update_settings_file()

        with open(project.settings_path) as f:
            lines = f.read().split('\n')

        assert "STATIC_URL = '/static/'" in lines
        assert "MEDIA_URL = '/media/'" in lines
        assert "STATIC_ROOT = os.path.join(BASE_DIR, 'static')" in lines
        assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines


    def test_adds_domain_to_ALLOWED_HOSTS(self):
        project = DjangoProject('mydomain.com', 'python.version')
        project.settings_path = Path(tempfile.NamedTemporaryFile().name)

        with open(project.settings_path, 'w') as f:
            f.write(dedent(
                """
                # settings file
                STATIC_URL = '/static/'
                ALLOWED_HOSTS = []
                """
            ))

        project.update_settings_file()

        with open(project.settings_path) as f:
            lines = f.read().split('\n')

        assert "ALLOWED_HOSTS = ['mydomain.com']" in lines



class TestRunCollectStatic:

    def test_runs_manage_py_in_correct_virtualenv(self, mock_subprocess, fake_home):
        project = DjangoProject('mydomain.com', 'python.version')
        project.virtualenv_path = Path('/path/to/virtualenv')
        project.manage_py_path = Path('/path/to/manage.py')
        project.run_collectstatic()
        assert mock_subprocess.check_call.call_args == call([
            project.virtualenv_path / 'bin/python',
            project.manage_py_path,
            'collectstatic',
            '--noinput'
        ])


class TestRunMigrate:

    def test_runs_manage_py_in_correct_virtualenv(self, mock_subprocess, fake_home):
        project = DjangoProject('mydomain.com', 'python.version')
        project.virtualenv_path = Path('/path/to/virtualenv')
        project.manage_py_path = Path('/path/to/manage.py')
        project.run_migrate()
        assert mock_subprocess.check_call.call_args == call([
            project.virtualenv_path / 'bin/python',
            project.manage_py_path,
            'migrate',
        ])


class TestUpdateWsgiFile:

    def test_updates_wsgi_file_from_template(self):
        project = DjangoProject('mydomain.com', 'python.version')
        project.wsgi_file_path = Path(tempfile.NamedTemporaryFile().name)
        project.settings_path = Path('/path/to/settingsfolder/settings.py')
        template = open(Path(pythonanywhere.django_project.__file__).parent / 'wsgi_file_template.py').read()

        project.update_wsgi_file()

        with open(project.wsgi_file_path) as f:
            contents = f.read()
        print(contents)
        assert contents == template.format(project=project)


    @pytest.mark.slowtest
    def test_actually_produces_wsgi_file_that_can_import_project_non_nested(
        self, fake_home, non_nested_submodule, virtualenvs_folder
    ):
        project = DjangoProject('mydomain.com', '3.6')
        shutil.copytree(non_nested_submodule, project.project_path)
        project.create_virtualenv()
        project.find_django_files()
        project.wsgi_file_path = Path(tempfile.NamedTemporaryFile().name)

        project.update_wsgi_file()

        print(open(project.wsgi_file_path).read())
        subprocess.check_output([project.virtualenv_path / 'bin/python', project.wsgi_file_path])


    @pytest.mark.slowtest
    def test_actually_produces_wsgi_file_that_can_import_nested_project(
        self, fake_home, more_nested_submodule, virtualenvs_folder
    ):
        project = DjangoProject('mydomain.com', '3.6')
        shutil.copytree(more_nested_submodule, project.project_path)
        project.create_virtualenv()
        project.find_django_files()
        project.wsgi_file_path = Path(tempfile.NamedTemporaryFile().name)

        project.update_wsgi_file()

        print(open(project.wsgi_file_path).read())
        subprocess.check_output([project.virtualenv_path / 'bin/python', project.wsgi_file_path])

