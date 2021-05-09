"""User interface for interacting with PythonAnywhere files.
Provides a class `PAPath` which should be used by helper scripts
providing features for programmatic handling of user's files."""

import getpass
import logging
from urllib.parse import urljoin

from pythonanywhere.api.files_api import Files
from pythonanywhere.snakesay import snakesay

logger = logging.getLogger("pythonanywhere")


class PAPath:
    """Class providing interface for interacting with PythonAnywhere
    user files.

    Class should be instantiated with a path to an existing
    PythonAnywhere file or directory that user has access to or to an
    available destination path for a file that would be uploaded.

    To get PythonAnywhere url for given path use
    :property:`PAPath.url`, to get its contents use
    :property:`PAPath.contents` or :property:`PAPath.tree` for a list
    of regular paths, when given path is directory.

    To perform actions on path pointing to an existing PythonAnywhere
    file/directory, use following methods:
    - :method:`PAPath.delete` to delete file/directory
    - :method:`PAPath.upload` to overwrite file contents
    - :method:`PAPath.share` to start sharing a file
    - :method:`PAPath.unshare` to stop sharing a file
    - :method:`PAPath.get_sharing_url` to check if file is already
    shared and get its sharing url

    When path does not represent existing PythonAnywhere file, it can
    be created with :method:`PAPath.upload`."""

    def __init__(self, path):
        self.path = self._standarize_path(path)
        self.api = Files()

    def __repr__(self):
        return self.url

    def _make_sharing_url(self, path):
        return urljoin(self.api.base_url.split("api")[0], path)

    @staticmethod
    def _standarize_path(path):
        return path.replace("~", f"/home/{getpass.getuser()}") if path.startswith("~") else path

    @property
    def url(self):
        """Returns url to PythonAnywhere for `self.path`.  Does not
        perform any checks (url might not point to an existing file)."""

        files_base = self.api.base_url.replace("/api/v0", "")
        return f"{files_base[:-1]}{self.path}"

    @property
    def contents(self):
        """When `self.path` points to a PythonAnywhere user
        directiory, returns a dictionary of its files and directories,
        where file/directory names are keys and values contain
        information about type and API endpoint.  Otherwise (when
        `self.path` points to a file) contents of the file are
        returned as bytes.

        >>> PAPath('/home/username').contents
        >>> {'.bashrc': {'type': 'file',
            'url': 'https://www.pythonanywhere.com/api/v0/user/username/files/path/home/username/.bashrc'},
            '.local': {'type': 'directory',
            'url': 'https://www.pythonanywhere.com/api/v0/user/username/files/path/home/username/.local'},
            ... }

        >>> PAPath('/home/username/README.txt').contents
        >>> b"some README.txt contents..."
        """

        try:
            content = self.api.path_get(self.path)
            return content if isinstance(content, dict) else content.decode("utf-8")
        except Exception as e:
            logger.warning(snakesay(str(e)))
            return None

    @property
    def tree(self):
        """Returns list of regular directories and files for
        `self.path`.  'Regular' means non dotfiles nor symlinks.
        Result is trimmed to 1000 items.

        >>> PAPath('/home/username').tree
        >>> ['/home/username/README.txt']
        """

        try:
            return self.api.tree_get(self.path)
        except Exception as e:
            logger.warning(snakesay(str(e)))
            return None

    def delete(self):
        """Returns `True` when `self.path` successfully deleted on
        PythonAnywhere, `False` otherwise."""

        try:
            self.api.path_delete(self.path)
            logger.info(snakesay(f"{self.path} deleted!"))
            return True
        except Exception as e:
            logger.warning(snakesay(str(e)))
            return False

    def upload(self, content):
        """Returns `True` when provided `content` successfully
        uploaded to `self.path`.  If `self.path` already existed on
        PythonAnywhere, it will be overwritten by the `content`.
        When upload is not successful, returns `False`."""

        try:
            result = self.api.path_post(self.path, content)
        except Exception as e:
            logger.warning(snakesay(str(e)))
            return False

        msg = {
            200: f"{self.path} successfully updated!",
            201: f"Content successfully uploaded to {self.path}!"
        }[result]

        logger.info(snakesay(msg))
        return True

    def get_sharing_url(self, quiet=False):
        """Returns PythonAnywhere sharing url for `self.path` if file
        is shared, empty string otherwise."""

        url = self.api.sharing_get(self.path)
        if url:
            sharing_url = self._make_sharing_url(url)
            if not quiet:
                logger.info(snakesay(f"{self.path} is shared at {sharing_url}"))
            return sharing_url

        logger.info(snakesay(f"{self.path} has not been shared"))

        return ""

    def share(self):
        """Returns PythonAnywhere sharing link for `self.path` or an
        empty string when share not successful."""

        try:
            code, url = self.api.sharing_post(self.path)
        except Exception as e:
            logger.warning(snakesay(str(e)))
            return ""

        msg = {200: "was already", 201: "successfully"}[code]
        sharing_url = self._make_sharing_url(url)
        logger.info(snakesay(f"{self.path} {msg} shared at {sharing_url}"))
        return sharing_url

    def unshare(self):
        """Returns `True` when file unshared or has not been shared,
        `False` otherwise."""

        already_shared = self.get_sharing_url(quiet=True)
        if already_shared:
            result = self.api.sharing_delete(self.path)
            if result == 204:
                logger.info(snakesay(f"{self.path} is no longer shared!"))
                return True
            logger.warning(snakesay(f"Could not unshare {self.path}... :("))
            return False
        logger.info(snakesay(f"{self.path} is not being shared, no need to stop sharing..."))
        return True
