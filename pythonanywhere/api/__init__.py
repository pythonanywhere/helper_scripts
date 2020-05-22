import warnings

from pythonanywhere.api.base import AuthenticationError, PYTHON_VERSIONS, call_api, get_api_endpoint
from pythonanywhere.api.webapp import Webapp

## TODO PEP 562 __getattr__ should be used here to handle deprecation warnings nicely when we drop python 3.6.
## See https://www.python.org/dev/peps/pep-0562/#id8

warnings.warn(
    """
    Importing from pythonanywhere.api is deprecated in favor of 
    pythonanywhere.api.base for call_api and get_api_endpoint
    and pythonanywhere.api.webapp for Webapp
    """,
    DeprecationWarning
)
