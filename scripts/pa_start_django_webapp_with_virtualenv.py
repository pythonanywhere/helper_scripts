#!/usr/bin/python3.5
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
import os

from pythonanywhere.snakesay import snakesay
from pythonanywhere.django_project import DjangoProject


def main(domain, django_version, python_version, nuke):
    if domain == 'your-username.pythonanywhere.com':
        username = getpass.getuser().lower()
        pa_domain = os.environ.get('PYTHONANYWHERE_DOMAIN', 'pythonanywhere.com')
        domain = '{username}.{pa_domain}'.format(username=username, pa_domain=pa_domain)

    project = DjangoProject(domain, python_version)
    project.sanity_checks(nuke=nuke)
    project.create_virtualenv(django_version, nuke=nuke)
    project.run_startproject(nuke=nuke)
    project.find_django_files()
    project.update_settings_file()
    project.run_collectstatic()
    project.create_webapp(nuke=nuke)
    project.add_static_file_mappings()

    project.update_wsgi_file()

    project.webapp.reload()

    print(snakesay('All done!  Your site is now live at https://{domain}'.format(domain=domain)))



if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['--domain'], arguments['--django'], arguments['--python'], nuke=arguments.get('--nuke'))
