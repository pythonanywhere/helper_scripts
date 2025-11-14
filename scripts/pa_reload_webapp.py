#!/usr/bin/python3.8
"""Reloads the given site

Usage:
  pa_reload_webapp.py <domain>

Options:
  <domain>              Domain name, eg www.mydomain.com
"""

from docopt import docopt

from pythonanywhere_core.exceptions import MissingCNAMEException
from pythonanywhere_core.webapp import Webapp
from snakesay import snakesay


def main(domain_name):
    webapp = Webapp(domain_name)
    try:
        webapp.reload()
    except MissingCNAMEException as e:
        print(snakesay(str(e)))
    print(snakesay(
        f"{domain_name} has been reloaded"
    ))


if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['<domain>'])
