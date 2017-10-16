#!/usr/bin/python3.6
"""Autoconfigure a Django project from on a github URL.

- downloads the repo
- creates a virtualenv and installs django (or detects a requirements.txt if available)
- creates webapp via api
- creates django wsgi configuration file
- adds static files config

Usage:
  pa_autoconfigure_django.py <git-repo-url> [--domain=<domain> --python=<python-version>] [--nuke]

Options:
  --domain=<domain>         Domain name, eg www.mydomain.com   [default: your-username.pythonanywhere.com]
  --python=<python-version> Python version, eg "2.7"    [default: 3.6]
  --nuke                    *Irrevocably* delete any existing web app config on this domain. Irrevocably.
"""

from docopt import docopt
import getpass
from pathlib import Path
import subprocess
import shutil

from pythonanywhere.django_project import DjangoProject
from pythonanywhere.snakesay import snakesay


def download_repo(repo, domain, nuke):
    target = Path('~').expanduser() / domain
    if nuke:
        shutil.rmtree(target)
    subprocess.check_call(['git', 'clone', repo, target])
    return target


def main(repo_url, domain, python_version, nuke):
    if domain == 'your-username.pythonanywhere.com':
        username = getpass.getuser().lower()
        domain = f'{username}.pythonanywhere.com'

    download_repo(repo_url, domain, nuke=nuke)

    project = DjangoProject(domain)
    project.sanity_checks(nuke=nuke)
    project.create_virtualenv(python_version, 'django', nuke=nuke)
    project.update_settings_file()
    project.run_collectstatic()
    project.create_webapp(nuke=nuke)
    project.update_wsgi_file()
    project.add_static_file_mappings()
    project.webapp.reload()

    print(snakesay(f'All done!  Your site is now live at https://{domain}'))





if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['<git-repo-url>'], arguments['--domain'], arguments['--python'], nuke=arguments.get('--nuke'))

