#!/usr/bin/python3.5
"""Reloads the given site

Usage:
  pa_reload_webapp.py <domain>

Options:
  <domain>              Domain name, eg www.mydomain.com
"""

from docopt import docopt
import os
import sys

from pythonanywhere.api import Webapp
from pythonanywhere.snakesay import snakesay


def main(domain_name):
    webapp = Webapp(domain_name)
    webapp.reload()
    print(snakesay(
        "{} has been reloaded".format(domain_name)
    ))


if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['<domain>'])
