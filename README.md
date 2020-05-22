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
    
## Contributing

Pull requests are welcome!  You'll find tests in the [tests](tests) folder...

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
