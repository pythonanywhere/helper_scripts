"""Interface speaking with PythonAnywhere API providing methods for
files.  *Don't use* `Files` :class: in helper scripts, use
`pythonanywhere.files.Path` class instead."""

import getpass
from urllib.parse import urljoin

from pythonanywhere.api.base import call_api, get_api_endpoint


class Files:
    """ Interface for PythonAnywhere files API.

    Uses `pythonanywhere.api.base` :method: `get_api_endpoint` to
    create url, which is stored in a class variable `Files.base_url`,
    then calls `call_api` with appropriate arguments to execute files
    action.

    Covers:
    - GET, POST and DELETE for files path endpoint
    - POST, GET and DELETE for files sharing endpoint
    - GET for tree endpoint

    "path" methods:
    - use :method: `Files.path_get` to get contents of file or
    directory from `path`
    - use :method: `Files.path_post` to upload or update file at given
    `dest_path` using contents from `source`
    - use :method: `Files.path_delete` to delete file/directory on on
    given `path`

    "sharing" methods:
    - use :method: `Files.sharing_post` to enable sharing a file from
    `path` (if not shared before) and get a link to it
    - use :method: `Files.sharing_get` to get sharing url for `path`
    - use :method: `Files.sharing_delete` to disable sharing for
    `path`

    "tree" method:
    - use :method: `Files.tree_get` to get list of regular files and
    subdirectories of a directory at `path` (limited to 1000 results)
    """

    base_url = get_api_endpoint().format(username=getpass.getuser(), flavor="files")
    path_endpoint = urljoin(base_url, "path")
    sharing_endpoint = urljoin(base_url, "sharing/")
    tree_endpoint = urljoin(base_url, "tree/")

    def _error_msg(self, result):
        """TODO: error responses should be unified at the API side """

        if "application/json" in result.headers.get("content-type", ""):
            jsn = result.json()
            msg = jsn.get("detail") or jsn.get("message") or jsn.get("error", "")
            return f": {msg}"
        return ""

    def path_get(self, path):
        """Returns dictionary of directory contents when `path` is an
        absolute path to of an existing directory or file contents if
        `path` is an absolute path to an existing file -- both
        available to the PythonAnywhere user.  Raises when `path` is
        invalid or unavailable."""

        url = f"{self.path_endpoint}{path}"

        result = call_api(url, "GET")

        if result.status_code == 200:
            if "application/json" in result.headers.get("content-type", ""):
                return result.json()
            return result.content

        raise Exception(
            f"GET to fetch contents of {url} failed, got {result}{self._error_msg(result)}"
        )

    def path_post(self, dest_path, content):
        """Uploads contents of `content` to `dest_path` which should be
        a valid absolute path of a file available to a PythonAnywhere
        user.  If `dest_path` contains directories which don't exist
        yet, they will be created.

        Returns 200 if existing file on PythonAnywhere has been
        updated with `source` contents, or 201 if file from
        `dest_path` has been created with those contents."""

        url = f"{self.path_endpoint}{dest_path}"

        result = call_api(url, "POST", files={"content": content})

        if result.ok:
            return result.status_code

        raise Exception(
            f"POST to upload contents to {url} failed, got {result}{self._error_msg(result)}"
        )

    def path_delete(self, path):
        """Deletes the file at specified `path` (if file is a
        directory it will be deleted as well).

        Returns 204 on sucess, raises otherwise."""

        url = f"{self.path_endpoint}{path}"

        result = call_api(url, "DELETE")

        if result.status_code == 204:
            return result.status_code

        raise Exception(
            f"DELETE on {url} failed, got {result}{self._error_msg(result)}"
        )

    def sharing_post(self, path):
        """Starts sharing a file at `path`.

        Returns a tuple with a status code and sharing link on
        success, raises otherwise.  Status code is 201 on success, 200
        if file has been already shared."""

        url = self.sharing_endpoint

        result = call_api(url, "POST", json={"path": path})

        if result.ok:
            return result.status_code, result.json()["url"]

        raise Exception(
            f"POST to {url} to share '{path}' failed, got {result}{self._error_msg(result)}"
        )

    def sharing_get(self, path):
        """Checks sharing status for a `path`.

        Returns url with sharing link if file is shared or an empty
        string otherwise."""

        url = f"{self.sharing_endpoint}?path={path}"

        result = call_api(url, "GET")

        return result.json()["url"] if result.ok else ""

    def sharing_delete(self, path):
        """Stops sharing file at `path`.

        Returns 204 on successful unshare."""

        url = f"{self.sharing_endpoint}?path={path}"

        result = call_api(url, "DELETE")

        return result.status_code

    def tree_get(self, path):
        """Returns list of absolute paths of regular files and
        subdirectories of a directory at `path`.  Result is limited to
        1000 items.

        Raises if `path` does not point to an existing directory."""

        url = f"{self.tree_endpoint}?path={path}"

        result = call_api(url, "GET")

        if result.ok:
            return result.json()

        raise Exception(f"GET to {url} failed, got {result}{self._error_msg(result)}")
