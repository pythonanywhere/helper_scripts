""" Interface speaking with PythonAnywhere API providing methods for files.
*Don't use* `Files` :class: in helper scripts, use `pythonanywhere.files` classes instead."""

import getpass
from urllib.parse import urljoin

from pythonanywhere.api.base import call_api, get_api_endpoint


class Files:
    """ Interface for PythonAnywhere files API.

    Uses `pythonanywhere.api.base` :method: `get_api_endpoint` to create url,
    which is stored in a class variable `Files.base_url`, then calls
    `call_api` with appropriate arguments to execute files action.

    Covers 'GET' for files path endpoint.

    **********************************
    TODOS:
    - POST, DELETE for path endpoint
    - POST for sharing
    - GET, DELETE for sharing path
    - GET for tree
    **********************************

    Use :method: `Files.get_path` to get contents of file or directory.
    """

    base_url = get_api_endpoint().format(username=getpass.getuser(), flavor="files")

    def get_path(self, path):
        url = urljoin(self.base_url, path)
        result = call_api(url, "GET")

        if result.status_code == 200:
            if "application/json" in result.headers.get("content-type", ""):
                return result.json()
            return result.content

        if not result.ok:
            raise Exception(
                f"GET to fetch contents of {url} failed, got {result}: {result.text}"
            )
