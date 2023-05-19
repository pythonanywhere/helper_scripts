"""Interface speaking with PythonAnywhere API providing methods for
students.  *Don't use* `StudentsAPI` :class: in helper scripts, use
`pythonanywhere.students.Students` class instead."""

import getpass

from pythonanywhere_core.base import call_api, get_api_endpoint


class StudentsAPI:
    """Interface for PythonAnywhere students API.

    Uses `pythonanywhere.api.base` :method: `get_api_endpoint` to
    create url, which is stored in a class variable `StudentsAPI.base_url`,
    then calls `call_api` with appropriate arguments to execute student
    action.

    Covers:
    - GET
    - DELETE

    Methods:
    - use :method: `StudentsAPI.get` to get list of students
    - use :method: `StudentsAPI.delete` to remove a student
    """

    base_url = get_api_endpoint().format(username=getpass.getuser(), flavor="students")

    def get(self):
        """Returns list of PythonAnywhere students related with user's account."""

        result = call_api(self.base_url, "GET")

        if result.status_code == 200:
            return result.json()

        raise Exception(f"GET to list students failed, got {result.text}")

    def delete(self, student_username):
        """Returns 204 if student has been successfully removed, raises otherwise."""

        url = f"{self.base_url}{student_username}"

        result = call_api(url, "DELETE")

        if result.status_code == 204:
            return result.status_code

        detail = f": {result.text}" if result.text else ""
        raise Exception(
            f"DELETE to remove student {student_username!r} failed, got {result}{detail}"
        )
