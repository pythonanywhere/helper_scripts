from pathlib import Path
from pythonanywhere.virtualenvs import create_virtualenv, Virtualenv


class TestVirtualenv:

    def test_path(self, virtualenvs_folder):
        v = Virtualenv('domain.com', 'python.version')
        assert v.path == Path(virtualenvs_folder) / 'domain.com'


    def test_create_uses_bash_and_sources_virtualenvwrapper(self, mock_subprocess):
        create_virtualenv('domain.com', '2.7', 'django', nuke=False)
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        assert command_list[:2] == ['bash', '-c']
        assert command_list[2].startswith('source virtualenvwrapper.sh && mkvirtualenv')


    def test_create_calls_mkvirtualenv_with_python_version_and_domain(self, mock_subprocess):
        create_virtualenv('domain.com', '2.7', 'django', nuke=False)
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        bash_command = command_list[2]
        assert 'mkvirtualenv --python=/usr/bin/python2.7 domain.com' in bash_command


    def test_create_pip_installs_packages(self, mock_subprocess):
        create_virtualenv('domain.com', '2.7', 'package1 package2==1.1.2', nuke=False)
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        assert command_list[2].endswith('pip install package1 package2==1.1.2')


    def test_create_returns_virtualenv_path(self, mock_subprocess, virtualenvs_folder):
        response = create_virtualenv('domain.com', '2.7', 'django', nuke=False)
        assert response == virtualenvs_folder / 'domain.com'


    def test_create_nuke_option_deletes_virtualenv_first(self, mock_subprocess, virtualenvs_folder):
        create_virtualenv('domain.com', '2.7', 'django', nuke=True)
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        assert command_list[:2] == ['bash', '-c']
        assert command_list[2].startswith('source virtualenvwrapper.sh && rmvirtualenv domain.com && mkvirtualenv')

