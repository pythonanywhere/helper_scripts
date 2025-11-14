#!/usr/bin/python3.8
"""Deletes webapp logs.

- gets list of logs via api
- deletes logs via api

Usage:
  pa_delete_webapp_logs.py [--domain=<domain>] [--log_type=<log_type>] [--log_index=<log_index>]

Options:
  --domain=<domain>         Domain name, eg www.mydomain.com   [default: your-username.pythonanywhere.com]
  --log_type=<log_type>     Log type, could be access, error, server or all   [default: all]
  --log_index=<log_index>   Log index, 0 for current log, 1-9 for one of archive logs or all [default: all]
"""

import os
from docopt import docopt
from pythonanywhere import __version__
from pythonanywhere_core.webapp import Webapp

os.environ["PYTHONANYWHERE_CLIENT"] = f"helper-scripts/{__version__}"
from snakesay import snakesay

from pythonanywhere.utils import ensure_domain, format_log_deletion_message


def main(domain, log_type, log_index):
    domain = ensure_domain(domain)
    webapp = Webapp(domain)
    log_types = ["access", "error", "server"]
    logs = webapp.get_log_info()
    if log_type == "all" and log_index == "all":
        for key in log_types:
            for log in logs[key]:
                print(snakesay(format_log_deletion_message(domain, key, log)))
                webapp.delete_log(key, log)
    elif log_type == "all":
        for key in log_types:
            print(snakesay(format_log_deletion_message(domain, key, int(log_index))))
            webapp.delete_log(key, int(log_index))
    elif log_index == "all":
        for i in logs[log_type]:
            print(snakesay(format_log_deletion_message(domain, log_type, i)))
            webapp.delete_log(log_type, int(i))
    else:
        print(snakesay(format_log_deletion_message(domain, log_type, int(log_index))))
        webapp.delete_log(log_type, int(log_index))
    print(snakesay('All Done!'))


if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['--domain'], arguments['--log_type'], arguments['--log_index'])
