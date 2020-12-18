"""User interface for interacting with PythonAnywhere files.
Provides a class `Path` which should be used by helper scripts
providing features for programmatic handling of user's files."""

import logging

from pythonanywhere.api.files_api import Files
from pythonanywhere.snakesay import snakesay

logger = logging.getLogger(name=__name__)


class Path:
    """Class providing interface for interacting with PythonAnywhere user files.
    """

    def __init__(self, path):
        self.path = path
        self.api = Files()

    def __repr__(self):
        user_url = self.api.base_url.replace("/api/v0", "")
        return f"{user_url}{self.path[1:]}"

    def contents(self):
        content = self.api.path_get(self.path)
        return content if type(content) == dict else content.decode("utf-8")

    def delete(self):
        try:
            self.api.path_delete(self.path)
            logger.info(snakesay(f"{self.path} deleted!"))
        except Exception as e:
            logger.warning(snakesay(str(e)))

    def upload(self):
        pass

    def share(self):
        pass

    def unshare(self):
        pass

    def tree(self):
        pass

