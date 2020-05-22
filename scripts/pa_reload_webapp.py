#!/usr/bin/python3.6
"""Reloads the given site

Usage:
  pa_reload_webapp.py <domain>

Options:
  <domain>              Domain name, eg www.mydomain.com
"""

from docopt import docopt

from pythonanywhere.api.webapp import Webapp
from pythonanywhere.snakesay import snakesay


def main(domain_name):
    webapp = Webapp(domain_name)
    webapp.reload()
    print(snakesay(
        f"{domain_name} has been reloaded"
    ))


if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['<domain>'])
