import pytest
from unittest.mock import call

from pythonanywhere.api.students_api import StudentsAPI
from pythonanywhere.students import Students


@pytest.mark.students
class TestStudentsInit:
    def test_instantiates_correctly(self):
        students = Students()
        assert type(students.api) == StudentsAPI


@pytest.mark.students
class TestStudentsGet:
    def test_returns_list_of_usernames_when_found_in_api_response(self, mocker):
        mock_students_api_get = mocker.patch("pythonanywhere.api.students_api.StudentsAPI.get")
        student_usernames = ["student1", "student2"]
        mock_students_api_get.return_value = {
            "students": [{"username": s} for s in student_usernames]
        }

        result = Students().get()

        assert mock_students_api_get.called
        assert result == student_usernames

    def test_returns_empty_list_when_no_usernames_found_in_api_response(self, mocker):
        mock_students_api_get = mocker.patch("pythonanywhere.api.students_api.StudentsAPI.get")
        mock_students_api_get.return_value = {"students": []}

        result = Students().get()

        assert mock_students_api_get.called
        assert result == []

    def test_uses_correct_grammar_in_log_messages(self, mocker, caplog):
        mock_students_api_get = mocker.patch("pythonanywhere.api.students_api.StudentsAPI.get")
        mock_students_api_get.return_value = {
            "students": [{"username": "one"}, {"username": "two"}]
        }

        Students().get()

        mock_students_api_get.return_value = {
            "students": [{"username": "one"}]
        }

        Students().get()

        first_log, second_log = caplog.records
        assert "students!" in first_log.message
        assert "student!" in second_log.message

@pytest.mark.students
class TestStudentsDelete:
    def test_returns_true_and_informs_when_student_removed(self, mocker):
        mock_students_api_delete = mocker.patch("pythonanywhere.api.students_api.StudentsAPI.delete")
        mock_students_api_delete.return_value = True
        mock_snake = mocker.patch("pythonanywhere.students.snakesay")
        mock_info =  mocker.patch("pythonanywhere.students.logger.info")
        student = "badstudent"

        result = Students().delete(student)

        assert mock_snake.call_args == call(f"{student!r} removed from the list of students!")
        assert mock_info.call_args == call(mock_snake.return_value)
        assert result is True

    def test_returns_false_and_warns_when_student_not_removed(self, mocker):
        mock_students_api_delete = mocker.patch("pythonanywhere.api.students_api.StudentsAPI.delete")
        mock_students_api_delete.side_effect = Exception("error msg")
        mock_students_api_delete.return_value = False
        mock_snake = mocker.patch("pythonanywhere.students.snakesay")
        mock_warning =  mocker.patch("pythonanywhere.students.logger.warning")
        student = "badstudent"

        result = Students().delete(student)

        assert mock_snake.call_args == call("error msg")
        assert mock_warning.call_args == call(mock_snake.return_value)
        assert result is False
