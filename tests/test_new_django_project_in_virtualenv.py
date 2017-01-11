import getpass
from unittest.mock import patch, call

from new_django_project_in_virtualenv import (
    create_virtualenv,
    create_webapp,
    main,
    start_django_project,
)


@patch('new_django_project_in_virtualenv.create_virtualenv')
@patch('new_django_project_in_virtualenv.start_django_project')
@patch('new_django_project_in_virtualenv.create_webapp')
class TestMain:

    def test_calls_create_virtualenv(
        self, mock_create_webapp, mock_start_django_project,
        mock_create_virtualenv
    ):
        main('domain', 'django.version', 'python.version')
        assert mock_create_virtualenv.call_args == call(
            'domain', 'python.version', 'django.version'
        )


    def test_domain_defaults_to_using_current_username(
        self, mock_create_webapp, mock_start_django_project,
        mock_create_virtualenv
    ):
        username = getpass.getuser()
        main('your-username.pythonanywhere.com', 'django.version', 'python.version')
        assert mock_create_virtualenv.call_args == call(
            username + '.pythonanywhere.com', 'python.version', 'django.version'
        )


    def test_calls_start_django_project_with_virtualenv(
        self, mock_create_webapp, mock_start_django_project,
        mock_create_virtualenv
    ):
        main('domain', 'django.version', 'python.version')
        assert mock_start_django_project.call_args == call(
            'domain', mock_create_virtualenv.return_value
        )


    def test_calls_create_webapp_with_virtualenv_and_python_version(
        self, mock_create_webapp, mock_start_django_project,
        mock_create_virtualenv
    ):
        main('domain', 'django.version', 'python.version')
        assert mock_create_webapp.call_args == call(
            'domain', 'python.version', mock_create_virtualenv.return_value, mock_start_django_project.return_value
        )

