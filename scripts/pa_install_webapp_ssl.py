#!/usr/bin/python3.5
"""Set the HTTPS certificate and private key for a website to the contents of two files, and reload the site.

Usage:
  pa_set_webapp_ssl.py <domain> <certificate-file> <private-key-file> [--suppress-reload]

Options:
  <domain>              Domain name, eg www.mydomain.com
  <certificate-file>    The name of the file containing the combined certificate in PEM format (normally
                        a number of blocks, each one starting "BEGIN CERTIFICATE" and ending "END CERTIFICATE")
  <private-key-file>    The name of the file containing the private key in PEM format (a file with one block,
                        starting with something like "BEGIN PRIVATE KEY" and ending with something like
                        "END PRIVATE KEY")
  --suppress-reload     The website will need to be reloaded in order to activate the new certificate/key combination
                        -- this happens by default, use this option to suppress it.
"""

from docopt import docopt
import os
import sys

from pythonanywhere.api import Webapp
from pythonanywhere.snakesay import snakesay


def main(domain_name, certificate_file, private_key_file, suppress_reload):
    if not os.path.exists(certificate_file):
        print("Could not find certificate file {certificate_file}".format(certificate_file=certificate_file))
        sys.exit(1)
    with open(certificate_file, "r") as f:
        certificate = f.read()

    if not os.path.exists(private_key_file):
        print("Could not find private key file {private_key_file}".format(private_key_file=private_key_file))
        sys.exit(1)
    with open(private_key_file, "r") as f:
        private_key = f.read()

    webapp = Webapp(domain_name)
    webapp.set_ssl(certificate, private_key)
    if not suppress_reload:
        webapp.reload()

    ssl_details = webapp.get_ssl_info()
    print(snakesay(
        "That's all set up now :-)\n"
        "Your new certificate will expire on {expiry:%d %B %Y},\n"
        "so shortly before then you should renew it\n"
        "and install the new certificate.".format(
            expiry=ssl_details["not_after"]
        )
    ))


if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(
        arguments['<domain>'],
        arguments['<certificate-file>'], arguments['<private-key-file>'],
        suppress_reload=arguments.get('--suppress-reload')
    )
