from unittest.mock import call, Mock

import pytest
from scripts.pa_delete_scheduled_task import main, _delete_all, _delete_by_id


@pytest.fixture
def task_list(mocker):
    mock_task_list = mocker.patch("scripts.pa_delete_scheduled_task.TaskList")
    mock_task1 = Mock(task_id=1)
    mock_task2 = Mock(task_id=2)
    mock_task_list.return_value.tasks = [mock_task1, mock_task2]
    return mock_task_list


@pytest.mark.tasks
class TestDeleteScheduledTaskDeleteALL:
    def test_deletes_all_tasks_with_user_permission(self, task_list, mocker):
        mock_input = mocker.patch("scripts.pa_delete_scheduled_task.input")
        mock_input.return_value = "y"

        _delete_all(force=False)

        assert mock_input.call_args == call(
            "This will irrevocably delete all your tasks, proceed? [y/N] "
        )
        assert task_list.call_count == 1
        for task in task_list.return_value.tasks:
            assert task.method_calls == [call.delete_schedule()]

    def test_exits_when_user_changes_mind(self, task_list, mocker):
        mock_input = mocker.patch("scripts.pa_delete_scheduled_task.input")
        mock_input.return_value = "n"

        _delete_all(force=False)

        assert task_list.call_count == 0

    def test_deletes_all_when_forced(self, task_list, mocker):
        mock_input = mocker.patch("scripts.pa_delete_scheduled_task.input")

        _delete_all(force=True)

        assert mock_input.call_count == 0
        assert task_list.call_count == 1
        for task in task_list.return_value.tasks:
            assert task.method_calls == [call.delete_schedule()]


@pytest.mark.tasks
class TestDeleteScheduledTaskDeleteById:
    def test_deletes_one_task(self, mocker):
        mock_task_from_id = mocker.patch("scripts.pa_delete_scheduled_task.get_task_from_id")

        _delete_by_id(id_numbers=[42])

        assert mock_task_from_id.call_args == call(42, no_exit=True)
        assert mock_task_from_id.return_value.method_calls == [call.delete_schedule()]

    def test_deletes_some_tasks(self, mocker):
        mock_task_from_id = mocker.patch("scripts.pa_delete_scheduled_task.get_task_from_id")

        _delete_by_id(id_numbers=[24, 42])

        assert mock_task_from_id.call_count == 2


@pytest.mark.tasks
class TestDeleteScheduledTaskMain:
    def test_sets_logger(self, mocker):
        mock_get_logger = mocker.patch("scripts.pa_delete_scheduled_task.get_logger")
        mock_delete_all = mocker.patch("scripts.pa_delete_scheduled_task._delete_all")
        mock_delete_by_id = mocker.patch("scripts.pa_delete_scheduled_task._delete_by_id")

        main(id_numbers=[1], nuke=False, force=None)

        mock_get_logger.call_count == 1

    def test_calls_delete_all(self, mocker):
        mock_delete_all = mocker.patch("scripts.pa_delete_scheduled_task._delete_all")
        mock_delete_by_id = mocker.patch("scripts.pa_delete_scheduled_task._delete_by_id")

        main(id_numbers=[], nuke=True, force=True)

        assert mock_delete_all.call_count == 1
        assert mock_delete_all.call_args == call(True)
        assert mock_delete_by_id.call_count == 0

    def test_calls_delete_by_id(self, mocker):
        mock_delete_all = mocker.patch("scripts.pa_delete_scheduled_task._delete_all")
        mock_delete_by_id = mocker.patch("scripts.pa_delete_scheduled_task._delete_by_id")

        main(id_numbers=[24, 42], nuke=False, force=None)

        assert mock_delete_all.call_count == 0
        assert mock_delete_by_id.call_count == 1
        assert mock_delete_by_id.call_args == call([24, 42])
