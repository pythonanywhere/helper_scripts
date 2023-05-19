import getpass
import json

import pytest
import responses

from pythonanywhere_core.base import get_api_endpoint
from pythonanywhere.api.students_api import StudentsAPI


@pytest.fixture
def students_base_url():
    return get_api_endpoint().format(username=getpass.getuser(), flavor="students")


@pytest.mark.students
class TestStudentsAPIGet:
    def test_gets_list_of_students_when_there_are_some(
        self, api_token, api_responses, students_base_url
    ):
        students = {
            "students": [{"username": "student1"}, {"username": "student2"}]
        }
        api_responses.add(
            responses.GET, url=students_base_url, status=200, body=json.dumps(students)
        )

        assert StudentsAPI().get() == students

    def test_gets_empty_list_of_students_when_there_none(
        self, api_token, api_responses, students_base_url
    ):
        students = {"students": []}
        api_responses.add(
            responses.GET, url=students_base_url, status=200, body=json.dumps(students)
        )

        assert StudentsAPI().get() == students


@pytest.mark.students
class TestStudentsAPIDelete:
    def test_returns_204_when_student_deleted(
        self, api_token, api_responses, students_base_url
    ):
        username = "byebye"
        url = f"{students_base_url}{username}"
        api_responses.add(responses.DELETE, url=url, status=204)

        assert StudentsAPI().delete("byebye") == 204

    def test_raises_with_404_when_no_student_to_delete_found(
        self, api_token, api_responses, students_base_url
    ):
        username = "notyourstudent"
        url = f"{students_base_url}{username}"
        api_responses.add(responses.DELETE, url=url, status=404)

        with pytest.raises(Exception) as e:
            StudentsAPI().delete("notyourstudent")

        expected_error_msg = (
            f"DELETE to remove student {username!r} failed, got <Response [404]>"
        )
        assert str(e.value) == expected_error_msg
