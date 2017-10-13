from unittest.mock import call, patch
from pathlib import Path
import tempfile
from textwrap import dedent

import pythonanywhere.django_project
from pythonanywhere.django_project import (
    start_django_project,
    update_settings_file,
    update_wsgi_file,
    DjangoProject,
)

class DjangoProjectTest:

    def test_project_path(self, mock_subprocess, fake_home):
        project = DjangoProject('mydomain.com', '/path/to/virtualenv')
        assert project.project_path == fake_home / 'mydomain.com'


class TestRunStartproject:

    def test_creates_folder(self, mock_subprocess, fake_home):
        project = DjangoProject('mydomain.com', '/path/to/virtualenv')
        project.run_startproject(nuke=False)
        assert (fake_home / 'mydomain.com').is_dir()


    def test_calls_startproject(self, mock_subprocess, fake_home):
        DjangoProject('mydomain.com', '/path/to/virtualenv').run_startproject(nuke=False)
        assert mock_subprocess.check_call.call_args == call([
            Path('/path/to/virtualenv/bin/django-admin.py'),
            'startproject',
            'mysite',
            fake_home / 'mydomain.com',
        ])


    def test_nuke_option_deletes_directory_first(self, mock_subprocess, fake_home):
        domain = 'mydomain.com'
        (fake_home / domain).mkdir()
        old_file = fake_home / domain / 'old_file.py'
        with open(old_file, 'w') as f:
            f.write('old stuff')

        DjangoProject(domain, '/path/to/virtualenv').run_startproject(nuke=True)  # should not raise

        assert not old_file.exists()



class TestUpdateSettingsFile:

    def test_adds_STATIC_and_MEDIA_config_to_settings(self):
        project = DjangoProject('mydomain.com', 'ignored')
        project.project_path = Path(tempfile.mkdtemp())
        (project.project_path / 'mysite').mkdir(parents=True)
        with open(project.project_path / 'mysite/settings.py', 'w') as f:
            f.write(dedent(
                """
                # settings file
                STATIC_URL = '/static/'
                ALLOWED_HOSTS = []
                """
            ))

        project.update_settings_file()

        with open(project.project_path / 'mysite/settings.py') as f:
            contents = f.read()

        lines = contents.split('\n')
        assert "STATIC_URL = '/static/'" in lines
        assert "MEDIA_URL = '/media/'" in lines
        assert "STATIC_ROOT = os.path.join(BASE_DIR, 'static')" in lines
        assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines


    def test_adds_domain_to_ALLOWED_HOSTS(self):
        project = DjangoProject('mydomain.com', 'ignored')
        project.project_path = Path(tempfile.mkdtemp())
        (project.project_path / 'mysite').mkdir(parents=True)
        with open(project.project_path / 'mysite/settings.py', 'w') as f:
            f.write(dedent(
                """
                # settings file
                STATIC_URL = '/static/'
                ALLOWED_HOSTS = []
                """
            ))

        project.update_settings_file()

        with open(project.project_path / 'mysite/settings.py') as f:
            contents = f.read()

        lines = contents.split('\n')

        assert "ALLOWED_HOSTS = ['mydomain.com']" in lines



class TestUpdateWsgiFile:

    def test_updates_wsgi_file_from_template(self):
        wsgi_file = tempfile.NamedTemporaryFile().name
        template = open(Path(pythonanywhere.django_project.__file__).parent / 'wsgi_file_template.py').read()

        update_wsgi_file(wsgi_file, '/project/path')

        with open(wsgi_file) as f:
            contents = f.read()
        assert contents == template.format(project_path='/project/path')

