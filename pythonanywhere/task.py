"""User interface for PythonAnywhere scheduled tasks. Provides two
classes: `Task` and `TaskList` which should be used by helper scripts
providing features for programmatic handling of scheduled task."""

import logging

from pythonanywhere.api.schedule import Schedule
from pythonanywhere.snakesay import snakesay

logger = logging.getLogger(name=__name__)


class Task:
    """Class representing PythonAnywhere scheduled task.

    Bare instance of the `Task` is just a 'blueprint' for a scheduled
    task. This means the proper way to create an object representing
    existing existing task or a task ready to be created a `Task` instance
    should be created using classmethod constructors: `Task.from_id`,
    `Task.to_be_created` or Task.from_api_specs`.

    To create new task use :classmethod:`Task.to_be_created` and call
    :method:`Task.create_schedule` on it.

    To get an object representing existing task its id is needed. Having a
    valid id call :classmethod:`Task.from_id` and then execute other
    actions on the task:
    - to delete the task use :method:`Task.delete_schedule`,
    - to update the task use :method:`Task.update_schedule`.

    :classmethod:`Task.from_api_specs` is intended to to be called with
    specs returned by API and should not be used with arbitrary specs
    defined by user.

    `Task` class is API agnostic meaning all API calls are made using the
    `pythonanywhere.api.schedule.Schedule` interface via `Task.schedule`
    attribute."""

    def __init__(self):
        self.command = None
        self.hour = None
        self.minute = None
        self.interval = None
        self.enabled = None
        self.task_id = None
        self.can_enable = None
        self.expiry = None
        self.extend_url = None
        self.logfile = None
        self.printable_time = None
        self.url = None
        self.user = None
        self.schedule = Schedule()

    def __repr__(self):
        enabled = "enabled" if self.enabled else "disabled"
        status = (
            f"{enabled} at {self.printable_time}"
            if self.printable_time
            else "ready to be created"
        )
        num = f" <{self.task_id}>:" if self.task_id else ""

        return f"{self.interval.title()} task{num} '{self.command}' {status}"

    @classmethod
    def from_id(cls, task_id):
        """Creates representation of existing scheduled task by id.

        :param task_id: existing task id as integer
        :returns: `Task` instance with actual specs."""

        task = cls()
        specs = task.schedule.get_specs(task_id)
        task.update_specs(specs)
        return task

    @classmethod
    def to_be_created(cls, *, command, minute, hour=None, disabled=False):
        """Creates object ready to be created via API.

        To create the task call :method:`Task.create_schedule` on it.
        :param command: command executed by the task
        :param minute: minute on which task will be executed (required)
        :param hour: hour on which daily task will be executed
            (required by daily tasks)
        :param disabled: set to True to create disabled task (default
            is True meaning task will be created as enabled)
        :returns: `Task` instance ready to be created"""

        if hour is not None and not (0 <= hour <= 23):
            raise ValueError("Hour has to be in 0..23")
        if not (0 <= minute <= 59):
            raise ValueError("Minute has to be in 0..59")

        task = cls()
        task.command = command
        task.hour = hour
        task.minute = minute
        task.interval = "daily" if hour is not None else "hourly"
        task.enabled = not disabled
        return task

    @classmethod
    def from_api_specs(cls, specs):
        """Create object representing scheduled task with specs returned by API.

        *Note* don't use this method in scripts. To create a new task use
        `Task.to_be_created` constructor.

        :param specs: spec dictionary returned by API.
        :returns: `Task` instance with actual specs."""

        task = cls()
        task.update_specs(specs)
        return task

    def update_specs(self, specs):
        """Sets `Task` instance's attributes using specs returned by API.

        *Note*: don't use this method in scripts.

        :param specs: spec dictionary returned by API."""

        for attr, value in specs.items():
            if attr == "id":
                attr = "task_id"
            setattr(self, attr, value)

    def create_schedule(self):
        """Creates new scheduled task.

        *Note* use this method on `Task.to_be_created` instance."""

        params = {
            "command": self.command,
            "enabled": self.enabled,
            "interval": self.interval,
            "minute": self.minute,
        }
        if self.hour is not None:
            params["hour"] = self.hour

        self.update_specs(self.schedule.create(params))

        mode = "will" if self.enabled else "may be enabled to"
        msg = (
            "Task '{command}' successfully created with id {task_id} "
            "and {mode} be run {interval} at {printable_time}"
        ).format(
            command=self.command,
            task_id=self.task_id,
            mode=mode,
            interval=self.interval,
            printable_time=self.printable_time,
        )
        logger.info(snakesay(msg))

    def delete_schedule(self):
        """Deletes existing task.

        *Note*: use this method on `Task.from_id` instance."""

        if self.schedule.delete(self.task_id):
            logger.info(snakesay(f"Task {self.task_id} deleted!"))

    def update_schedule(self, params, *, porcelain=False):
        """Updates existing task using `params`.

        *Note*: use this method on `Task.from_id` instance.

        `params` should be one at least one of: command, enabled, interval,
        hour, minute. `interval` takes precedence over `hour` meaning that
        `hour` param will be ignored if `interval` is set to 'hourly'.

        :param params: dictionary of specs to update
        :param porcelain: when True don't use `snakesay` in stdout messages
            (defaults to False)"""

        specs = {
            "command": self.command,
            "enabled": self.enabled,
            "interval": self.interval,
            "hour": self.hour,
            "minute": self.minute,
        }

        specs.update(params)

        if (
            (specs["interval"] != "daily")
            or (params.get("interval") == "daily" and self.hour)
            or (params.get("hour") == self.hour)
        ):
            specs.pop("hour")

        if params.get("minute") == self.minute:
            specs.pop("minute")

        new_specs = self.schedule.update(self.task_id, specs)

        diff = {
            key: (getattr(self, key), new_specs[key])
            for key in specs
            if getattr(self, key) != new_specs[key]
        }

        def make_spec_str(key, old_spec, new_spec):
            return f"<{key}> from '{old_spec}' to '{new_spec}'"

        updated = [make_spec_str(key, val[0], val[1]) for key, val in diff.items()]

        def make_msg(join_with):
            fill = " " if join_with == ", " else join_with
            intro = f"Task {self.task_id} updated:{fill}"
            return f"{intro}{join_with.join(updated)}"

        if updated:
            if porcelain:
                logger.info(make_msg(join_with="\n"))
            else:
                logger.info(snakesay(make_msg(join_with=", ")))
            self.update_specs(new_specs)
        else:
            logger.warning(snakesay("Nothing to update!"))


class TaskList:
    """Creates user's tasks representation using `Task` class and specs
    returned by API.

    Tasks are stored in `TaskList.tasks` variable."""

    def __init__(self):
        self.tasks = [Task.from_api_specs(specs) for specs in Schedule().get_list()]
