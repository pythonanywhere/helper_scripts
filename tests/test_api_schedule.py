import getpass
import json

import pytest
import responses

from pythonanywhere_core.base import get_api_endpoint
from pythonanywhere.api.schedule import Schedule


@pytest.fixture
def task_base_url():
    return get_api_endpoint().format(username=getpass.getuser(), flavor="schedule")


@pytest.fixture
def task_specs():
    username = getpass.getuser()
    return {
        "can_enable": False,
        "command": "echo foo",
        "enabled": True,
        "expiry": None,
        "extend_url": f"/user/{username}/schedule/task/123/extend",
        "hour": 16,
        "id": 123,
        "interval": "daily",
        "logfile": "/user/{username}/files/var/log/tasklog-126708-daily-at-1600-echo_foo.log",
        "minute": 0,
        "printable_time": "16:00",
        "url": f"/api/v0/user/{username}/schedule/123",
        "user": username,
    }


@pytest.fixture
def hourly_task_params():
    return {
        "command": "echo foo",
        "enabled": True,
        "interval": "hourly",
        "minute": 0,
    }


@pytest.fixture
def daily_task_params(hourly_task_params):
    return hourly_task_params.update({"interval": "daily", "hour": 16})


@pytest.mark.tasks
class TestScheduleCreate:
    def test_creates_daily_task(
        self, api_token, api_responses, task_specs, daily_task_params, task_base_url
    ):
        api_responses.add(
            responses.POST, url=task_base_url, status=201, body=json.dumps(task_specs)
        )

        assert Schedule().create(daily_task_params) == task_specs

    def test_creates_hourly_task(
        self, api_token, api_responses, task_specs, hourly_task_params, task_base_url
    ):
        hourly_specs = {"hour": None, "interval": "hourly", "printable_time": "00 minutes past"}
        task_specs.update(hourly_specs)
        api_responses.add(
            responses.POST, url=task_base_url, status=201, body=json.dumps(task_specs)
        )

        assert Schedule().create(hourly_task_params) == task_specs

    def test_raises_because_missing_params(self, api_token, api_responses, task_base_url):
        body = (
            '{"interval":["This field is required."],"command":["This field is required."],'
            '"minute":["This field is required."]}'
        )
        api_responses.add(responses.POST, url=task_base_url, status=400, body=body)

        with pytest.raises(Exception) as e:
            Schedule().create({})

        expected_error_msg = "POST to set new task via API failed, got <Response [400]>: " + body
        assert str(e.value) == expected_error_msg


@pytest.mark.tasks
class TestScheduleDelete:
    def test_deletes_task(self, api_token, api_responses, task_base_url):
        url = task_base_url + "42/"
        api_responses.add(responses.DELETE, url=url, status=204)

        result = Schedule().delete(42)

        post = api_responses.calls[0]
        assert post.request.url == url
        assert post.request.body is None
        assert result is True

    def test_raises_because_attempt_to_delete_nonexisting_task(
        self, api_token, api_responses, task_base_url
    ):
        body = '{"detail": "Not fount."}'
        api_responses.add(
            responses.DELETE, url=task_base_url + "42/", status=404, body=body,
        )

        with pytest.raises(Exception) as e:
            Schedule().delete(42)

        assert str(e.value) == "DELETE via API on task 42 failed, got <Response [404]>: " + body


@pytest.mark.tasks
class TestScheduleGetSpecs:
    def test_returns_spec_dict(self, api_token, api_responses, task_base_url, task_specs):
        api_responses.add(
            responses.GET, url=task_base_url + "123/", status=200, body=json.dumps(task_specs)
        )

        assert Schedule().get_specs(123) == task_specs

    def test_raises_because_attempt_to_get_nonexisting_task(
        self, api_token, api_responses, task_base_url
    ):
        body = '{"detail":"Not found."}'
        api_responses.add(responses.GET, url=task_base_url + "42/", status=404, body=body)

        with pytest.raises(Exception) as e:
            Schedule().get_specs(42)

        expected_error_msg = "Could not get task with id 42. Got result <Response [404]>: " + body
        assert str(e.value) == expected_error_msg


@pytest.mark.tasks
class TestScheduleGetList:
    def test_returns_tasks_list(self, api_token, api_responses, task_base_url):
        fake_specs = [{"fake": "specs"}, {"and": "more"}]
        api_responses.add(
            responses.GET, url=task_base_url, status=200, body=json.dumps(fake_specs),
        )

        assert Schedule().get_list() == fake_specs


@pytest.mark.tasks
class TestScheduleUpdate:
    def test_updates_daily_task(
        self, api_token, api_responses, task_specs, daily_task_params, task_base_url
    ):
        api_responses.add(
            responses.PATCH, url=task_base_url + "123/", status=200, body=json.dumps(task_specs),
        )

        assert Schedule().update(123, daily_task_params) == task_specs

    def test_raises_when_wrong_params(
        self, api_token, api_responses, task_specs, daily_task_params, task_base_url
    ):
        body = '{"non_field_errors":["Hourly tasks must not have an hour."]}'
        api_responses.add(responses.PATCH, url=task_base_url + "1/", status=400, body=body)

        with pytest.raises(Exception) as e:
            Schedule().update(1, {"hour": 23})

        assert str(e.value) == "Could not update task 1. Got <Response [400]>: " + body
