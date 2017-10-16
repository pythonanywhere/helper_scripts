from unittest.mock import call, patch
import getpass

from scripts.pa_autoconfigure_django import main



class TestMain:

    def test_calls_all_stuff_in_right_order(self):
        with patch('scripts.pa_autoconfigure_django.DjangoProject') as mock_DjangoProject:
            main(
                'https://github.com/pythonanywhere.com/example-django-project.git',
                'www.domain.com',
                'python.version',
                nuke='nuke option'
            )
        assert mock_DjangoProject.call_args == call('www.domain.com')
        assert mock_DjangoProject.return_value.method_calls == [
            call.sanity_checks(nuke='nuke option'),
            call.download_repo('https://github.com/pythonanywhere.com/example-django-project.git', nuke='nuke option'),
            call.create_virtualenv('python.version', nuke='nuke option'),
            call.update_settings_file(),
            call.run_collectstatic(),
            call.create_webapp(nuke='nuke option'),
            call.update_wsgi_file(),
            call.add_static_file_mappings(),
            call.webapp.reload()
        ]


    def test_domain_defaults_to_using_current_username(self):
        username = getpass.getuser()
        with patch('scripts.pa_autoconfigure_django.DjangoProject') as mock_DjangoProject:
            main('a-repo', 'your-username.pythonanywhere.com', 'python.version', nuke=False)
        assert mock_DjangoProject.call_args == call(
            username + '.pythonanywhere.com'
        )


    def test_lowercases_username(self):
        with patch('scripts.pa_autoconfigure_django.getpass') as mock_getpass:
            mock_getpass.getuser.return_value = 'UserName1'
            with patch('scripts.pa_autoconfigure_django.DjangoProject') as mock_DjangoProject:
                main('a-url', 'your-username.pythonanywhere.com', 'python.version', 'nukey')
            assert mock_DjangoProject.call_args == call(
                'username1.pythonanywhere.com',
            )



def test_todos():
    assert not 'existing-project sanity checks eg settings.py not found, requirements empty'
    assert not 'SECRET_KEY'
    assert not 'database stuff?'

