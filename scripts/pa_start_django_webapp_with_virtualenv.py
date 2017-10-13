#!/usr/bin/python3.6
"""Create a new Django webapp with a virtualenv.  Defaults to
your free domain, the latest version of Django and Python 3.6

Usage:
  pa_start_django_webapp_with_virtualenv.py [--domain=<domain> --django=<django-version> --python=<python-version>] [--nuke]

Options:
  --domain=<domain>         Domain name, eg www.mydomain.com   [default: your-username.pythonanywhere.com]
  --django=<django-version> Django version, eg "1.8.4"  [default: latest]
  --python=<python-version> Python version, eg "2.7"    [default: 3.6]
  --nuke                    *Irrevocably* delete any existing web app config on this domain. Irrevocably.
"""

from docopt import docopt
import getpass

from pythonanywhere.snakesay import snakesay
from pythonanywhere.api import (
    add_static_file_mappings,
    create_webapp,
    reload_webapp,
)

from pythonanywhere.virtualenvs import create_virtualenv
from pythonanywhere.django_project import DjangoProject
from pythonanywhere.sanity_checks import sanity_checks


def main(domain, django_version, python_version, nuke):
    if domain == 'your-username.pythonanywhere.com':
        username = getpass.getuser().lower()
        domain = f'{username}.pythonanywhere.com'
    sanity_checks(domain, nuke=nuke)
    packages = 'django' if django_version == 'latest' else f'django=={django_version}'
    virtualenv = create_virtualenv(domain, python_version, packages, nuke=nuke)

    project = DjangoProject(domain, virtualenv)
    project.run_startproject(nuke=nuke)
    project.update_settings_file()
    project.run_collectstatic()

    create_webapp(domain, python_version, virtualenv, project.project_path, nuke=nuke)
    add_static_file_mappings(domain, project.project_path)

    project.update_wsgi_file()

    reload_webapp(domain)

    print(snakesay(f'All done!  Your site is now live at https://{domain}'))



if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['--domain'], arguments['--django'], arguments['--python'], nuke=arguments.get('--nuke'))

