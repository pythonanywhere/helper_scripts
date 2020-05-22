""" Interface speaking with PythonAnywhere API providing methods for scheduled tasks.
*Don't use* `Schedule` :class: in helper scripts, use `task.Task` instead."""

import getpass

from pythonanywhere.api.base import call_api, get_api_endpoint


class Schedule:
    """Interface for PythonAnywhere scheduled tasks API.

    Uses `pythonanywhere.api` :method: `get_api_endpoint` to create url,
    which is stored in a class variable `Schedule.base_url`, then calls
    `call_api` with appropriate arguments to execute scheduled tasks tasks
    actions. Covers 'GET' and 'POST' methods for tasks list, as well as
    'GET', 'PATCH' and 'DELETE' methods for task with id.

    Use :method: `Schedule.get_list` to get all tasks list.
    Use :method: `Schedule.create` to create new task.
    Use :method: `Schedule.get_specs` to get existing task specs.
    Use :method: `Schedule.delete` to delete existing task.
    Use :method: `Schedule.update` to update existing task."""

    base_url = get_api_endpoint().format(username=getpass.getuser(), flavor="schedule")

    def get_list(self):
        """Gets list of existing scheduled tasks.

        :returns: list of existing scheduled tasks specs"""

        return call_api(self.base_url, "GET").json()

    def create(self, params):
        """Creates new scheduled task using `params`.

        Params should be: command, enabled (True or False), interval (daily or
        hourly), hour (24h format) and minute.

        :param params: dictionary with required scheduled task specs
        :returns: dictionary with created task specs"""

        result = call_api(self.base_url, "POST", json=params)

        if result.status_code == 201:
            return result.json()

        if not result.ok:
            raise Exception(
                f"POST to set new task via API failed, got {result}: {result.text}"
            )

    def get_specs(self, task_id):
        """Get task specs by id.

        :param task_id: existing task id
        :returns: dictionary of existing task specs"""

        result = call_api(
            f"{self.base_url}{task_id}/", "GET"
        )
        if result.status_code == 200:
            return result.json()
        else:
            raise Exception(
                "Could not get task with id {task_id}. Got result {result}: {content}".format(
                    task_id=task_id, result=result, content=result.text
                )
            )

    def delete(self, task_id):
        """Deletes scheduled task by id.

        :param task_id: scheduled task to be deleted id number
        :returns: True when API response is 204"""

        result = call_api(
            f"{self.base_url}{task_id}/", "DELETE"
        )

        if result.status_code == 204:
            return True

        if not result.ok:
            raise Exception(
                f"DELETE via API on task {task_id} failed, got {result}: {result.text}"
            )

    def update(self, task_id, params):
        """Updates existing task using id and params.

        Params should at least one of: command, enabled, interval, hour,
        minute. To update hourly task don't use 'hour' param. On the other
        hand when changing task's interval from 'hourly' to 'daily' hour is
        required.

        :param task_id: existing task id
        :param params: dictionary of specs to update"""

        result = call_api(
            f"{self.base_url}{task_id}/",
            "PATCH",
            json=params,
        )
        if result.status_code == 200:
            return result.json()
        else:
            raise Exception(
                f"Could not update task {task_id}. Got {result}: {result.text}"
            )
