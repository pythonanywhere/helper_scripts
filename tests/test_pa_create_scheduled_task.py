from unittest.mock import call

import pytest
from scripts.pa_create_scheduled_task import main


@pytest.mark.tasks
def test_checks_method_calls_and_args(mocker):
    mock_Task = mocker.patch("scripts.pa_create_scheduled_task.Task.to_be_created")

    main(command="echo foo", hour=8, minute=10, disabled=False)

    assert mock_Task.call_args == call(command="echo foo", hour=8, minute=10, disabled=False)
    assert mock_Task.return_value.method_calls == [call.create_schedule()]
