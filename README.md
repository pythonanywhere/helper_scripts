[![Build Status](https://travis-ci.org/pythonanywhere/helper_scripts.svg?branch=master)](https://travis-ci.org/pythonanywhere/helper_scripts)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/pythonanywhere)](https://pypi.org/project/pythonanywhere/)
[![Downloads](https://pepy.tech/badge/pythonanywhere)](https://pepy.tech/project/pythonanywhere)

# PythonAnywhere helper scripts

These scripts are designed to be run from PythonAnywhere consoles

## Installing

    pip3.6 install --user pythonanywhere

If there is no `python3.6` on your PythonAnywhere account, 
you should contact [support@pythonanywhere.com](mailto:support@pythonanywhere.com) and ask for an upgrade. 
    
## Usage

There are two ways to use that package. You can just run the scripts or use underlying api wrappers directly in your scripts.

There are scripts provided for dealing with web apps: 

* [pa_autoconfigure_django.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_autoconfigure_django.py)
* [pa_create_webapp_with_virtualenv.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_create_webapp_with_virtualenv.py)
* [pa_delete_webapp_logs.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_delete_webapp_logs.py)
* [pa_install_webapp_letsencrypt_ssl.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_install_webapp_letsencrypt_ssl.py)
* [pa_install_webapp_ssl.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_install_webapp_ssl.py)
* [pa_reload_webapp.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_reload_webapp.py)
* [pa_start_django_webapp_with_virtualenv.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_start_django_webapp_with_virtualenv.py)

and scheduled tasks:

* [pa_create_scheduled_task.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_create_scheduled_task.py)
* [pa_delete_scheduled_task.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_delete_scheduled_task.py)
* [pa_get_scheduled_tasks_list.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_get_scheduled_tasks_list.py)
* [pa_get_scheduled_task_specs.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_get_scheduled_task_specs.py)
* [pa_update_scheduled_task.py](https://github.com/pythonanywhere/helper_scripts/blob/master/scripts/pa_update_scheduled_task.py)

Run any of them with `--help` flag to get information about usage.   

See the [blog post](https://blog.pythonanywhere.com/155/)

## Contributing

Pull requests are welcome!  You'll find tests in the [tests](https://github.com/pythonanywhere/helper_scripts/blob/master/tests) folder...

    # prep your dev environment
    mkvirtualenv --python=python3.6 helper_scripts
    pip install -r requirements.txt
    pip install -e .

    # running the tests:
    pytest

    # make sure that the code that you have written is well tested:
    pytest --cov=pythonanywhere --cov=scripts

    # to just run the fast tests:
    pytest -m 'not slowtest' -v

