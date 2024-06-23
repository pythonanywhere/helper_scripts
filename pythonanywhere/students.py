"""User interface for Pythonanywhere students API.

Provides a class `Students` which should be used by helper scripts
providing features for programmatic listing and removing of the user's
students.
"""

import logging

from snakesay import snakesay

from pythonanywhere_core.students import StudentsAPI

logger = logging.getLogger("pythonanywhere")


class Students:
    """Class providing interface for PythonAnywhere students API.

    To perform actions on students related with user's account, use
    following methods:
    - :method:`Students.get` to get a list of students
    - :method:`Students.delete` to remove a student with a given username
    """

    def __init__(self):
        self.api = StudentsAPI()

    def get(self):
        """
        Returns list of usernames when user has students, otherwise an
        empty list.
        """

        try:
            result = self.api.get()
            student_usernames = [student["username"] for student in result["students"]]
            count = len(student_usernames)
            if count:
                msg = f"You have {count} student{'s' if count > 1 else ''}!"
            else:
                msg = "Currently you don't have any students."
            logger.info(snakesay(msg))
            return student_usernames
        except Exception as e:
            logger.warning(snakesay(str(e)))

    def delete(self, username):
        """
        Returns `True` when user with `username` successfully removed from
        user's students list, `False` otherwise.
        """

        try:
            self.api.delete(username)
            logger.info(snakesay(f"{username!r} removed from the list of students!"))
            return True
        except Exception as e:
            logger.warning(snakesay(str(e)))
            return False
