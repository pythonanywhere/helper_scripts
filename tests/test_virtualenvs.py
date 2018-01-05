from pathlib import Path
from pythonanywhere.virtualenvs import Virtualenv


class TestVirtualenv:

    def test_path(self, virtualenvs_folder):
        v = Virtualenv('domain.com', 'python.version')
        assert v.path == Path(virtualenvs_folder) / 'domain.com'


    def test_create_uses_bash_and_sources_virtualenvwrapper(self, mock_subprocess):
        v = Virtualenv('domain.com', '2.7')
        v.create(nuke=False)
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        assert command_list[:2] == ['bash', '-c']
        assert command_list[2].startswith('source virtualenvwrapper.sh && mkvirtualenv')


    def test_create_calls_mkvirtualenv_with_python_version_and_domain(self, mock_subprocess):
        v = Virtualenv('domain.com', '2.7')
        v.create(nuke=False)
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        bash_command = command_list[2]
        assert 'mkvirtualenv --python=/usr/bin/python2.7 domain.com' in bash_command


    def test_nuke_option_deletes_virtualenv(self, mock_subprocess, virtualenvs_folder):
        v = Virtualenv('domain.com', '2.7')
        v.create(nuke=True)
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        assert command_list[:2] == ['bash', '-c']
        assert command_list[2].startswith('source virtualenvwrapper.sh && rmvirtualenv domain.com')


    def test_install_pip_installs_packages(self, mock_subprocess):
        packages = 'package1 package2==1.1.2'
        v = Virtualenv('domain.com', '2.7')
        v.create(nuke=False)
        v.pip_install(packages)
        args, kwargs = mock_subprocess.check_call.call_args_list[-1]
        command_list = args[0]
        pip_path = str(v.path / 'bin/pip')
        assert command_list == [pip_path, 'install', packages]


