# PythonAnywhere helper scripts

These scripts are made available in */bin* on [PythonAnywhere](https://www.pythonanywhere.com/)


## Contributing

Pull requests are welcome!  You'll find tests in the [tests](tests) folder...

    # prep your dev environment
    mkvirtualenv --python=python3.6 helper_scripts
    pip install -r requirements.txt
    pip install -e .

    # running the tests:
    pytest

    # to just run the fast tests:
    pytest -m 'not slowtest' --tb=short -v 

