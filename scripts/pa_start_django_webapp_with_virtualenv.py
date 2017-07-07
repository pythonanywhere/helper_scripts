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
import os
from textwrap import dedent

from pythonanywhere.snakesay import snakesay
from pythonanywhere.api import (
    API_ENDPOINT,
    add_static_file_mappings,
    call_api,
    create_webapp,
    reload_webapp,
)

from pythonanywhere.virtualenvs import _virtualenv_path, create_virtualenv
from pythonanywhere.django_project import (
    _project_folder,
    start_django_project,
    update_settings_file,
    run_collectstatic,
    update_wsgi_file,
)


class SanityException(Exception):
    pass


def sanity_checks(domain, nuke):
    print(snakesay('Running sanity checks'))
    token = os.environ.get('API_TOKEN')
    if not token:
        raise SanityException(dedent(
            '''
            Could not find your API token.
            You may need to create it on the Accounts page?
            You will also need to close this console and open a new one once you've done that.
            '''
        ))

    if nuke:
        return
    url = API_ENDPOINT.format(username=getpass.getuser()) + domain + '/'
    response = call_api(url, 'get')
    if response.status_code == 200:
        raise SanityException(f'You already have a webapp for {domain}.\n\nUse the --nuke option if you want to replace it.')
    if os.path.exists(_virtualenv_path(domain)):
        raise SanityException(f'You already have a virtualenv for {domain}.\n\nUse the --nuke option if you want to replace it.')
    project_folder = _project_folder(domain)
    if os.path.exists(project_folder):
        raise SanityException(f'You already have a project folder at {project_folder}.\n\nUse the --nuke option if you want to replace it.')




def main(domain, django_version, python_version, nuke):
    if domain == 'your-username.pythonanywhere.com':
        username = getpass.getuser().lower()
        domain = f'{username}.pythonanywhere.com'
    sanity_checks(domain, nuke=nuke)
    virtualenv_path = create_virtualenv(domain, python_version, django_version, nuke=nuke)
    project_path = start_django_project(domain, virtualenv_path, nuke=nuke)
    update_settings_file(domain, project_path)
    run_collectstatic(virtualenv_path, project_path)
    create_webapp(domain, python_version, virtualenv_path, project_path, nuke=nuke)
    add_static_file_mappings(domain, project_path)
    wsgi_file_path = '/var/www/' + domain.replace('.', '_') + '_wsgi.py'
    update_wsgi_file(wsgi_file_path, project_path)
    reload_webapp(domain)

    print(snakesay(f'All done!  Your site is now live at https://{domain}'))



if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['--domain'], arguments['--django'], arguments['--python'], nuke=arguments.get('--nuke'))

