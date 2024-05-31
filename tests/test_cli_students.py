import pytest
from typer.testing import CliRunner
from unittest.mock import call

from cli.students import app

runner = CliRunner()


@pytest.fixture
def mock_students(mocker):
    return mocker.patch("cli.students.Students", autospec=True)


@pytest.fixture
def mock_students_get(mock_students):
    return mock_students.return_value.get


@pytest.fixture
def mock_students_delete(mock_students):
    return mock_students.return_value.delete


def test_main_subcommand_without_args_prints_help():
    result = runner.invoke(
        app,
        [],
    )
    assert result.exit_code == 0
    assert "Show this message and exit." in result.stdout


@pytest.mark.students
class TestGet:
    def test_exits_early_with_error_when_api_does_not_return_expected_list(
            self, mock_students_get
    ):
        mock_students_get.return_value = None

        result = runner.invoke(app, ["get"])

        assert result.exit_code == 1

    def test_exits_early_with_error_when_api_returns_empty_list(self, mock_students_get):
        mock_students_get.return_value = []

        result = runner.invoke(app, ["get"])

        assert result.exit_code == 1

    def test_prints_list_of_students_when_students_found(self, mock_students_get):
        students_found = ["one", "two", "three"]
        mock_students_get.return_value = students_found

        result = runner.invoke(app, ["get"])

        assert result.exit_code == 0
        assert "\n".join(students_found) in result.stdout

    def test_prints_numbered_list_of_students_when_students_found_and_numbered_flag_used(
            self, mock_students_get
    ):
        students_found = ["one", "two", "three"]
        mock_students_get.return_value = students_found

        result = runner.invoke(app, ["get", "--numbered"])

        assert result.exit_code == 0
        assert "1. one" in result.stdout
        assert "2. two" in result.stdout
        assert "3. three" in result.stdout

    def test_prints_repr_of_list_returned_by_the_api_when_raw_flag_used(self, mock_students_get):
        mock_students_get.return_value = ["one", "two", "three"]

        result = runner.invoke(app, ["get", "--raw"])

        assert result.exit_code == 0
        assert "['one', 'two', 'three']" in result.stdout

    def test_prints_sorted_list_of_students_returned_by_the_api_when_sort_flag_used(
            self, mock_students_get
    ):
        mock_students_get.return_value = ["one", "two", "three"]

        result = runner.invoke(app, ["get", "--sort"])

        assert result.exit_code == 0
        assert "one\nthree\ntwo" in result.stdout

    def test_prints_reversed_sorted_list_of_students_returned_by_the_api_when_sort_reverse_flag_used(
            self, mock_students_get
    ):
        mock_students_get.return_value = ["one", "two", "three"]

        result = runner.invoke(app, ["get", "--reverse"])

        assert result.exit_code == 0
        assert "two\nthree\none" in result.stdout


@pytest.mark.students
class TestDelete:
    def test_exits_with_success_when_provided_student_removed(self, mock_students_delete):
        mock_students_delete.return_value = True

        result = runner.invoke(app, ["delete", "thisStudent"])

        assert result.exit_code == 0
        assert mock_students_delete.call_args_list ==  [call("thisStudent")]


    def test_exits_with_error_when_no_student_removed(self, mock_students_delete):
        mock_students_delete.return_value = False

        result = runner.invoke(app, ["delete", "thisStudent"])

        assert result.exit_code == 1


@pytest.mark.students
class TestHolidays:
    def test_exits_with_success_when_all_students_removed(
            self, mock_students_get, mock_students_delete
    ):
        students = ["one", "two", "three"]
        mock_students_get.return_value = students
        mock_students_delete.side_effect = [True for _ in students]

        result = runner.invoke(app, ["holidays"])

        assert result.exit_code == 0
        assert mock_students_delete.call_args_list == [call(s) for s in students]
        assert "Removed all 3 students" in result.stdout

    def test_exits_with_error_when_none_student_removed(
            self, mock_students_get, mock_students_delete
    ):
        mock_students_get.return_value = []

        result = runner.invoke(app, ["holidays"])

        assert result.exit_code == 1
        assert not mock_students_delete.called
