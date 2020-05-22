#!/usr/bin/python3.6
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

from docopt import docopt

from pythonanywhere.api.webapp import Webapp
from pythonanywhere.snakesay import snakesay
from pythonanywhere.utils import ensure_domain


def main(domain, log_type, log_index):
    webapp = Webapp(ensure_domain(domain))
    log_types = ["access", "error", "server"]
    logs = webapp.get_log_info()
    if log_type == "all" and log_index == "all":
        for key in log_types:
            for log in logs[key]:
                webapp.delete_log(key, log)
    elif log_type == "all":
        for key in log_types:
            webapp.delete_log(key, int(log_index))
    elif log_index == "all":
        for i in logs[log_type]:
            webapp.delete_log(log_type, int(i))
    else:
        webapp.delete_log(log_type, int(log_index))
    print(snakesay('All Done!'))


if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['--domain'], arguments['--log_type'], arguments['--log_index'])
