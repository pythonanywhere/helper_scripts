[![Build Status](https://travis-ci.org/pythonanywhere/helper_scripts.svg?branch=master)](https://travis-ci.org/pythonanywhere/helper_scripts)

# PythonAnywhere helper scripts

These scripts are designed to be run from PythonAnywhere consoles


## Installing


    pip3.5 install --user pythonanywhere


## Contributing

Pull requests are welcome!  You'll find tests in the [tests](tests) folder...

    # prep your dev environment
    mkvirtualenv --python=python3.5 helper_scripts
    pip install -r requirements.txt
    pip install -e .

    # running the tests:
    pytest

    # to just run the fast tests:
    pytest -m 'not slowtest' -v

