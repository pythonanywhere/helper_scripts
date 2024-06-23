import pytest
from unittest.mock import call

from pythonanywhere_core.students import StudentsAPI
from pythonanywhere.students import Students


@pytest.mark.students
class TestStudentsInit:
    def test_instantiates_correctly(self):
        students = Students()
        assert isinstance(students.api, StudentsAPI)


@pytest.mark.students
class TestStudentsGet:
    def test_returns_list_of_usernames_when_found_in_api_response(self, mocker):
        mock_students_api_get = mocker.patch("pythonanywhere.students.StudentsAPI.get")
        student_usernames = ["student1", "student2"]
        mock_students_api_get.return_value = {
            "students": [{"username": s} for s in student_usernames]
        }

        result = Students().get()

        assert mock_students_api_get.called
        assert result == student_usernames

    def test_returns_empty_list_when_no_usernames_found_in_api_response(self, mocker):
        mock_students_api_get = mocker.patch("pythonanywhere.students.StudentsAPI.get")
        mock_students_api_get.return_value = {"students": []}

        result = Students().get()

        assert mock_students_api_get.called
        assert result == []

    @pytest.mark.parametrize(
        "api_response,expected_wording",
        [
            ({"students": [{"username": "one"}, {"username": "two"}]}, "You have 2 students!"),
            ({"students": [{"username": "one"}]}, "You have 1 student!"),
        ]
    )
    def test_uses_correct_grammar_in_log_messages(self, mocker, api_response, expected_wording):
        mock_students_api_get = mocker.patch("pythonanywhere.students.StudentsAPI.get")
        mock_students_api_get.return_value = api_response
        mock_snake = mocker.patch("pythonanywhere.students.snakesay")
        mock_info =  mocker.patch("pythonanywhere.students.logger.info")

        Students().get()

        assert mock_snake.call_args == call(expected_wording)
        assert mock_info.call_args == call(mock_snake.return_value)


@pytest.mark.students
class TestStudentsDelete:
    def test_returns_true_and_informs_when_student_removed(self, mocker):
        mock_students_api_delete = mocker.patch("pythonanywhere.students.StudentsAPI.delete")
        mock_students_api_delete.return_value = True
        mock_snake = mocker.patch("pythonanywhere.students.snakesay")
        mock_info =  mocker.patch("pythonanywhere.students.logger.info")
        student = "badstudent"

        result = Students().delete(student)

        assert mock_snake.call_args == call(f"{student!r} removed from the list of students!")
        assert mock_info.call_args == call(mock_snake.return_value)
        assert result is True

    def test_returns_false_and_warns_when_student_not_removed(self, mocker):
        mock_students_api_delete = mocker.patch("pythonanywhere.students.StudentsAPI.delete")
        mock_students_api_delete.side_effect = Exception("error msg")
        mock_students_api_delete.return_value = False
        mock_snake = mocker.patch("pythonanywhere.students.snakesay")
        mock_warning =  mocker.patch("pythonanywhere.students.logger.warning")
        student = "badstudent"

        result = Students().delete(student)

        assert mock_snake.call_args == call("error msg")
        assert mock_warning.call_args == call(mock_snake.return_value)
        assert result is False
