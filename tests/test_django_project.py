import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from platform import python_version
from textwrap import dedent
from unittest.mock import Mock, call

import pytest

import pythonanywhere.django_project
from pythonanywhere.django_project import DjangoProject
from pythonanywhere.exceptions import SanityException


class TestDownloadRepo:
    @pytest.mark.slowtest
    def test_actually_downloads_repo(self, fake_home):
        repo = "https://gist.github.com/hjwp/4173bcface139beb7632ec93726f91ea"
        project = DjangoProject("www.a.domain.com", "py.version")
        project.download_repo(repo, nuke=False)
        assert project.project_path.is_dir()
        assert "file1.py" in os.listdir(str(project.project_path))
        assert "file2.py" in os.listdir(str(project.project_path))

    def test_calls_git_subprocess(self, mock_subprocess, fake_home):
        project = DjangoProject("www.a.domain.com", "py.version")
        project.download_repo("repo", nuke=False)
        assert mock_subprocess.check_call.call_args == call(["git", "clone", "repo", str(project.project_path)])

    def test_nuke_option_deletes_directory_first(self, mock_subprocess, fake_home):
        project = DjangoProject("www.a.domain.com", "py.version")
        project.project_path.mkdir()
        (project.project_path / "old-thing.txt").touch()
        mock_subprocess.check_call.side_effect = lambda *_, **__: Path(project.project_path).mkdir()

        project.download_repo("repo", nuke=True)
        assert "old-thing.txt" not in project.project_path.iterdir()

    def test_nuke_option_ignores_directory_doesnt_exist(self, mock_subprocess, fake_home):
        project = DjangoProject("www.a.domain.com", "py.version")
        mock_subprocess.check_call.side_effect = lambda *_, **__: Path(project.project_path).mkdir()

        project.download_repo("repo", nuke=True)  # should not raise

        assert project.project_path.is_dir()


class TestDetectDjangoVersion:
    def test_is_versionless_django_by_default(self, fake_home):
        project = DjangoProject("mydomain.com", "python.version")
        assert project.detect_requirements() == "django"

    def test_if_requirements_txt_exists(self, fake_home):
        project = DjangoProject("mydomain.com", "python.version")
        project.project_path.mkdir()
        requirements_txt = project.project_path / "requirements.txt"
        requirements_txt.touch()
        assert project.detect_requirements() == "-r {requirements_txt}".format(
            requirements_txt=requirements_txt.resolve()
        )


@pytest.fixture
def project_with_mock_virtualenv(virtualenvs_folder):
    project = DjangoProject("mydomain.com", "python.version")
    project.virtualenv.create = Mock()
    project.virtualenv.pip_install = Mock()
    yield project


class TestCreateVirtualenv:
    def test_calls_virtualenv_create(self, project_with_mock_virtualenv):
        project_with_mock_virtualenv.create_virtualenv("django.version", nuke="nuke option")
        assert project_with_mock_virtualenv.virtualenv.create.call_args == call(nuke="nuke option")

    def test_calls_pip_install_with_django_version_if_specified(self, project_with_mock_virtualenv):
        project_with_mock_virtualenv.create_virtualenv("django.version", nuke="nuke option")
        assert project_with_mock_virtualenv.virtualenv.pip_install.call_args == call("django==django.version")

    def test_special_cases_latest_django_version(self, project_with_mock_virtualenv):
        project_with_mock_virtualenv.create_virtualenv("latest", nuke="nuke option")
        assert project_with_mock_virtualenv.virtualenv.pip_install.call_args == call("django")

    def test_uses_detect_if_django_version_not_specified(self, project_with_mock_virtualenv):
        project_with_mock_virtualenv.detect_requirements = Mock()
        project_with_mock_virtualenv.create_virtualenv(nuke="nuke option")
        assert project_with_mock_virtualenv.virtualenv.pip_install.call_args == call(
            project_with_mock_virtualenv.detect_requirements.return_value
        )


class TestRunStartproject:
    def test_creates_folder(self, mock_subprocess, fake_home):
        project = DjangoProject("mydomain.com", "python.version")
        project.run_startproject(nuke=False)
        assert (fake_home / "mydomain.com").is_dir()

    def test_calls_startproject(self, mock_subprocess, fake_home):
        project = DjangoProject("mydomain.com", "python.version")
        project.run_startproject(nuke=False)
        assert mock_subprocess.check_call.call_args == call(
            [
                str(Path(project.virtualenv.path / "bin/django-admin.py")),
                "startproject",
                "mysite",
                str(fake_home / "mydomain.com"),
            ]
        )

    def test_nuke_option_deletes_directory_first(self, mock_subprocess, fake_home):
        project = DjangoProject("mydomain.com", "python.version")
        (fake_home / project.domain).mkdir()
        old_file = fake_home / project.domain / "old_file.py"
        old_file.write_text("old stuff")

        project.run_startproject(nuke=True)

        assert not old_file.exists()

    def test_nuke_option_handles_directory_not_existing(self, mock_subprocess, fake_home):
        project = DjangoProject("mydomain.com", "python.version")
        project.run_startproject(nuke=True)  # should not raise


@pytest.fixture
def non_nested_submodule():
    subprocess.check_call(["git", "submodule", "update", "--init", "--recursive"])
    submodule_path = Path(__file__).parents[1] / "submodules" / "example-django-project"
    subprocess.check_call(["git", "checkout", "master"], cwd=str(submodule_path))
    yield submodule_path
    subprocess.check_call(["git", "submodule", "update", "--init", "--recursive"])


@pytest.fixture
def more_nested_submodule():
    subprocess.check_call(["git", "submodule", "update", "--init", "--recursive"])
    submodule_path = Path(__file__).parents[1] / "submodules" / "example-django-project"
    subprocess.check_call(["git", "checkout", "morenested"], cwd=str(submodule_path))
    yield submodule_path
    subprocess.check_call(["git", "submodule", "update", "--init", "--recursive"])


class TestFindDjangoFiles:
    def test_non_nested(self, fake_home, non_nested_submodule):
        project = DjangoProject("mydomain.com", "python.version")
        shutil.copytree(str(non_nested_submodule), str(project.project_path))
        expected_settings_path = project.project_path / "myproject/settings.py"
        assert expected_settings_path.exists()
        expected_manage_py = project.project_path / "manage.py"
        assert expected_manage_py.exists()

        project.find_django_files()

        assert project.settings_path == expected_settings_path
        assert project.manage_py_path == expected_manage_py

    def test_nested(self, fake_home, more_nested_submodule):
        project = DjangoProject("mydomain.com", "python.version")
        shutil.copytree(str(more_nested_submodule), str(project.project_path))
        expected_settings_path = project.project_path / "mysite/mysite/settings.py"
        assert expected_settings_path.exists()
        expected_manage_py = project.project_path / "mysite/manage.py"
        assert expected_manage_py.exists()

        project.find_django_files()

        assert project.settings_path == expected_settings_path
        assert project.manage_py_path == expected_manage_py

    def test_raises_if_empty_project_folder(self, fake_home):
        project = DjangoProject("mydomain.com", "python.version")
        with pytest.raises(SanityException) as e:
            project.find_django_files()

        assert "Could not find your settings.py" in str(e.value)

    def test_raises_if_no_settings_in_any_subfolders(self, fake_home):
        project = DjangoProject("mydomain.com", "python.version")
        not_this_folder = project.project_path / "not_this_folder"
        not_this_folder.mkdir(parents=True)
        with pytest.raises(SanityException) as e:
            project.find_django_files()

        assert "Could not find your settings.py" in str(e.value)

    def test_raises_if_manage_py_not_found(self, fake_home, non_nested_submodule):
        project = DjangoProject("mydomain.com", "python.version")
        shutil.copytree(str(non_nested_submodule), str(project.project_path))
        expected_manage_py = project.project_path / "manage.py"
        assert expected_manage_py.exists()
        expected_manage_py.unlink()
        with pytest.raises(SanityException) as e:
            project.find_django_files()

        assert "Could not find your manage.py" in str(e.value)


class TestUpdateSettingsFile:
    def test_adds_STATIC_and_MEDIA_config_to_settings(self):
        project = DjangoProject("mydomain.com", "python.version")
        project.settings_path = Path(tempfile.NamedTemporaryFile().name)

        with project.settings_path.open("w") as f:
            f.write(
                dedent(
                    """
                # settings file
                STATIC_URL = '/static/'
                ALLOWED_HOSTS = []
                """
                )
            )

        project.update_settings_file()

        with project.settings_path.open() as f:
            lines = f.read().split("\n")

        assert "STATIC_URL = '/static/'" in lines
        assert "MEDIA_URL = '/media/'" in lines
        assert "STATIC_ROOT = os.path.join(BASE_DIR, 'static')" in lines
        assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines

    def test_adds_domain_to_ALLOWED_HOSTS(self):
        project = DjangoProject("mydomain.com", "python.version")
        project.settings_path = Path(tempfile.NamedTemporaryFile().name)

        with project.settings_path.open("w") as f:
            f.write(
                dedent(
                    """
                # settings file
                STATIC_URL = '/static/'
                ALLOWED_HOSTS = []
                """
                )
            )

        project.update_settings_file()

        with project.settings_path.open() as f:
            lines = f.read().split("\n")

        assert "ALLOWED_HOSTS = ['mydomain.com']" in lines


class TestRunCollectStatic:
    def test_runs_manage_py_in_correct_virtualenv(self, mock_subprocess, fake_home):
        project = DjangoProject("mydomain.com", "python.version")
        project.manage_py_path = Path("/path/to/manage.py")
        project.run_collectstatic()
        assert mock_subprocess.check_call.call_args == call(
            [str(project.virtualenv.path / "bin/python"), str(project.manage_py_path), "collectstatic", "--noinput"]
        )


class TestRunMigrate:
    def test_runs_manage_py_in_correct_virtualenv(self, mock_subprocess, fake_home):
        project = DjangoProject("mydomain.com", "python.version")
        project.manage_py_path = Path("/path/to/manage.py")
        project.run_migrate()
        assert mock_subprocess.check_call.call_args == call(
            [str(project.virtualenv.path / "bin/python"), str(project.manage_py_path), "migrate"]
        )


class TestUpdateWsgiFile:
    def test_updates_wsgi_file_from_template(self):
        project = DjangoProject("mydomain.com", "python.version")
        project.wsgi_file_path = Path(tempfile.NamedTemporaryFile().name)
        project.settings_path = Path("/path/to/settingsfolder/settings.py")
        template = (Path(pythonanywhere.django_project.__file__).parent / "wsgi_file_template.py").open().read()

        project.update_wsgi_file()

        with project.wsgi_file_path.open() as f:
            contents = f.read()
        print(contents)
        assert contents == template.format(project=project)

    @pytest.mark.slowtest
    def test_actually_produces_wsgi_file_that_can_import_project_non_nested(
        self, fake_home, non_nested_submodule, virtualenvs_folder
    ):
        running_python_version = ".".join(python_version().split(".")[:2])
        project = DjangoProject("mydomain.com", running_python_version)
        shutil.copytree(str(non_nested_submodule), str(project.project_path))
        if running_python_version in ["3.7", "3.8"]:
            project.create_virtualenv(django_version="latest")
        else:
            project.create_virtualenv()
        project.find_django_files()
        project.wsgi_file_path = Path(tempfile.NamedTemporaryFile().name)

        project.update_wsgi_file()

        print(project.wsgi_file_path.open().read())
        subprocess.check_output([str(project.virtualenv.path / "bin/python"), str(project.wsgi_file_path)])

    @pytest.mark.slowtest
    def test_actually_produces_wsgi_file_that_can_import_nested_project(
        self, fake_home, more_nested_submodule, virtualenvs_folder
    ):
        running_python_version = ".".join(python_version().split(".")[:2])
        project = DjangoProject("mydomain.com", running_python_version)
        shutil.copytree(str(more_nested_submodule), str(project.project_path))
        if running_python_version in ["3.7", "3.8"]:
            project.create_virtualenv(django_version="latest")
        else:
            project.create_virtualenv()
        project.find_django_files()
        project.wsgi_file_path = Path(tempfile.NamedTemporaryFile().name)

        project.update_wsgi_file()

        print(project.wsgi_file_path.open().read())
        subprocess.check_output([str(project.virtualenv.path / "bin/python"), str(project.wsgi_file_path)])
