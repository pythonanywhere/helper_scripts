from pathlib import Path
import re
import shutil
import subprocess

from packaging import version

from pythonanywhere.exceptions import SanityException
from pythonanywhere.snakesay import snakesay
from .project import Project


class DjangoProject(Project):
    def django_version_newer_or_equal_than(self, this_version):
        return version.parse(self.virtualenv.get_version("django")) >= version.parse(this_version)

    def download_repo(self, repo, nuke):
        if nuke and self.project_path.exists():
            shutil.rmtree(str(self.project_path))
        subprocess.check_call(['git', 'clone', repo, str(self.project_path)])

    def ensure_branch(self, branch):
        output = subprocess.check_output(
            ["git", "-C", str(self.project_path), "branch", "-r"]
        ).decode().rstrip().split("\n")
        branches = [x.strip().replace("origin/", "") for x in output if "->" not in x]
        if branch == "None" and len(branches) == 1:
            return
        if branch == "None":
            shutil.rmtree(str(self.project_path))
            raise SanityException(
                "There are many branches in your repo. "
                "You need to specify which branch to use by adding "
                "--branch=<branch> option to the command."
            )
        if branch not in branches:
            shutil.rmtree(str(self.project_path))
            raise SanityException(f"You do not have a {branch} branch in your repo")
        #
        current_branch = subprocess.check_output(
            ["git", "-C", str(self.project_path), "rev-parse", "--abbrev-ref HEAD"]
        ).decode().strip()

        if current_branch != branch:
            subprocess.check_call(["git", "-C", str(self.project_path), "checkout", branch])

    def create_virtualenv(self, django_version=None, nuke=False):
        self.virtualenv.create(nuke=nuke)
        if django_version is None:
            packages = self.detect_requirements()
        elif django_version == 'latest':
            packages = 'django'
        else:
            packages = f'django=={django_version}'
        self.virtualenv.pip_install(packages)

    def detect_requirements(self):
        requirements_txt = self.project_path / 'requirements.txt'
        if requirements_txt.exists():
            return f'-r {requirements_txt.resolve()}'
        return 'django'

    def run_startproject(self, nuke):
        print(snakesay('Starting Django project'))
        if nuke and self.project_path.exists():
            shutil.rmtree(str(self.project_path))
        self.project_path.mkdir()

        new_django = self.django_version_newer_or_equal_than("4.0")
        django_admin_executable = "django-admin" if new_django else "django-admin.py"

        subprocess.check_call([
            str(Path(self.virtualenv.path) / "bin" / django_admin_executable),
            "startproject",
            "mysite",
            str(self.project_path),
        ])


    def find_django_files(self):
        try:
            self.settings_path = next(self.project_path.glob('**/settings.py'))
        except StopIteration:
            raise SanityException('Could not find your settings.py')
        try:
            self.manage_py_path = next(self.project_path.glob('**/manage.py'))
        except StopIteration:
            raise SanityException('Could not find your manage.py')


    def update_settings_file(self):
        print(snakesay('Updating settings.py'))

        with self.settings_path.open() as f:
            settings = f.read()
        new_settings = settings.replace(
            'ALLOWED_HOSTS = []',
            f'ALLOWED_HOSTS = [{self.domain!r}]'
        )

        new_django = self.django_version_newer_or_equal_than("3.1")

        if re.search(r'^MEDIA_ROOT\s*=', settings, flags=re.MULTILINE) is None:
            new_settings += "\nMEDIA_URL = '/media/'"
        if re.search(r'^STATIC_ROOT\s*=', settings, flags=re.MULTILINE) is None:
            if new_django:
                new_settings += "\nSTATIC_ROOT = Path(BASE_DIR / 'static')"
            else:
                new_settings += "\nSTATIC_ROOT = os.path.join(BASE_DIR, 'static')"
        if re.search(r'^MEDIA_ROOT\s*=', settings, flags=re.MULTILINE) is None:
            if new_django:
                new_settings += "\nMEDIA_ROOT = Path(BASE_DIR / 'media')"
            else:
                new_settings += "\nMEDIA_ROOT = os.path.join(BASE_DIR, 'media')"

        with self.settings_path.open('w') as f:
            f.write(new_settings)


    def run_collectstatic(self):
        print(snakesay('Running collectstatic'))
        subprocess.check_call([
            str(Path(self.virtualenv.path) / 'bin/python'),
            str(self.manage_py_path),
            'collectstatic',
            '--noinput',
        ])


    def run_migrate(self):
        print(snakesay('Running migrate database'))
        subprocess.check_call([
            str(Path(self.virtualenv.path) / 'bin/python'),
            str(self.manage_py_path),
            'migrate',
        ])


    def update_wsgi_file(self):
        print(snakesay(f'Updating wsgi file at {self.wsgi_file_path}'))
        template = (Path(__file__).parent / 'wsgi_file_template.py').open().read()
        with self.wsgi_file_path.open('w') as f:
            f.write(template.format(project=self))
