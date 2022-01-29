![Build Status](https://github.com/pythonanywhere/helper_scripts/actions/workflows/tests.yaml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/pythonanywhere)](https://pypi.org/project/pythonanywhere/)
[![Downloads](https://pepy.tech/badge/pythonanywhere)](https://pepy.tech/project/pythonanywhere)

# PythonAnywhere cli tool

`pa` is a single command to manage PythonAnywhere services. 

It is designed to be run from PythonAnywhere consoles, but many subcommands can be executed directly 
from your own machine (see [usage](#Usage) below). 

## Installing
### On PythonAnywhere
In a PythonAnywhere Bash console, run: 

    pip3.9 install --user pythonanywhere

If there is no `python3.9` on your PythonAnywhere account, 
you should upgrade your account to the newest system image.
See [here](https://help.pythonanywhere.com/pages/ChangingSystemImage) how to do that.
`pa` works with python 3.6, 3.7 and 3.8, but we recommend using the latest system image.

### On your own machine
Install the `pythonanywhere` package from [PyPI](https://pypi.org/project/pythonanywhere/). 
We recommend using `pipx` if you want to use it only as a cli tool, or a virtual environment 
if you want to use a programmatic interface in your own code.

## Usage

There are two ways to use the package. You can just run the scripts or use the underlying api wrappers directly in your scripts.

### Command line interface

### Running `pa` on your local machine

`pa` expects the presence of some environment variables that are provided when you run your code in a PythonAnywere console.
You need to provide them if you run `pa` on your local machine.

`API_TOKEN` -- you need to set this to allow `pa` to connect to the [PythonAnywere API](https://help.pythonanywhere.com/pages/API). 
To get an API token, log into PythonAnywhere and go to the "Account" page using the link at the top right. 
Click on the "API token" tab, and click the "Create a new API token" button to get your token.

`PYTHONANYWHERE_SITE` is used to connect to PythonAnywhere API and defaults to `www.pythonanywhere.com`, 
but you may need to set it to `eu.pythonanywhere.com` if you use our EU site.   

If your username on PythonAnywhere is different from the username on your local machine, 
you may need to set `USER` for the environment you run `pa` in.   

### Programmatic usage in your code

Take a look at the [`pythonanywhere.task`](https://github.com/pythonanywhere/helper_scripts/blob/master/pythonanywhere/task.py) 
module and docstrings of `pythonanywhere.task.Task` class and its methods.   

### Legacy scripts

Some legacy [scripts](https://github.com/pythonanywhere/helper_scripts/blob/master/legacy.md) (separate for each action) are still available.

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

