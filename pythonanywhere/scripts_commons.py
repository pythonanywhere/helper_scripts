"""Helpers used by pythonanywhere helper scripts."""

import logging
import sys

from schema import And, Or, Schema, SchemaError, Use

from pythonanywhere.snakesay import snakesay
from pythonanywhere.task import Task

logger = logging.getLogger(__name__)

# fmt: off
tabulate_formats = [
    "plain", "simple", "github", "grid", "fancy_grid", "pipe", "orgtbl", "jira",
    "presto", "psql", "rst", "mediawiki", "moinmoin", "youtrack", "html", "latex",
    "latex_raw", "latex_booktabs", "textile",
]
# fmt: on


class ScriptSchema(Schema):
    """Extends `Schema` adapting it to PA scripts validation strategies.

    Adds predefined schemata as class variables to be used in scripts'
    validation schemas as well as `validate_user_input` method which acts
    as `Schema.validate` but returns a dictionary with converted keys
    ready to be used as function keyword arguments, e.g. validated
    arguments {"--foo": bar, "<baz>": qux} will be be converted to
    {"foo": bar, "baz": qux}. Additional conversion rules may be added as
    dictionary passed to `validate_user_input` :method: as `conversions`
    :param:.

    Use :method:`ScriptSchema.validate_user_input` to obtain kwarg
    dictionary."""

    # class variables are used in task scripts schemata:
    boolean = Or(None, bool)
    hour = Or(None, And(Use(int), lambda h: 0 <= h <= 23), error="--hour has to be in 0..23")
    id_multi = Or([], And(lambda y: [x.isdigit() for x in y], error="<id> has to be integer"))
    id_required = And(Use(int), error="<id> has to be an integer")
    minute_required = And(Use(int), lambda m: 0 <= m <= 59, error="--minute has to be in 0..59")
    minute = Or(None, minute_required)
    string = Or(None, str)
    tabulate_format = Or(
        None,
        And(str, lambda f: f in tabulate_formats),
        error=f"--format should match one of: {', '.join(tabulate_formats)}",
    )

    replacements = {"--": "", "<": "", ">": ""}

    def convert(self, string):
        """Removes cli argument notation characters ('--', '<', '>' etc.).

        :param string: cli argument key to be converted to fit Python
        argument syntax."""

        for key, value in self.replacements.items():
            string = string.replace(key, value)
        return string

    def validate_user_input(self, arguments, *, conversions=None):
        """Calls `Schema.validate` on provided `arguments`.

        Returns dictionary with keys converted by
        `ScriptSchema.convert` :method: to be later used as kwarg
        arguments. Universal rules for conversion are stored in
        `replacements` class variable and may be updated using
        `conversions` kwarg. Use optional `conversions` :param: to add
        custom replacement rules.

        :param arguments: dictionary of cli arguments provided be
        (e.g.) `docopt`
        :param conversions: dictionary of additional rules to
        `self.replacements`"""

        if conversions:
            self.replacements.update(conversions)

        try:
            self.validate(arguments)
            return {self.convert(key): val for key, val in arguments.items()}
        except SchemaError as e:
            logger.warning(snakesay(str(e)))
            sys.exit(1)


def get_logger(set_info=False):
    """Sets logger for 'pythonanywhere' package.

    Returns `logging.Logger` instance with no message formatting which
    will stream to stdout. With `set_info` :param: set to `True`
    logger defines `logging.INFO` level otherwise it leaves default
    `logging.WARNING`.

    To toggle message visibility in scripts use `logger.info` calls
    and switch `set_info` value accordingly.

    :param set_info: boolean (defaults to False)"""

    logging.basicConfig(format="%(message)s", stream=sys.stdout)
    logger = logging.getLogger("pythonanywhere")
    if set_info:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
    return logger


def get_task_from_id(task_id, no_exit=False):
    """Get `Task.from_id` instance representing existing task.

    :param task_id: integer (should be a valid task id)
    :param no_exit: if (default) False sys.exit will be called when
      exception is caught"""

    try:
        return Task.from_id(task_id)
    except Exception as e:
        logger.warning(snakesay(str(e)))
        if not no_exit:
            sys.exit(1)
