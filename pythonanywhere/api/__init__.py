import warnings

from pythonanywhere.api.base import AuthenticationError, PYTHON_VERSIONS, call_api, get_api_endpoint
from pythonanywhere.api.webapp import Webapp

warnings.warn(
    """
    Importing from pythonanywhere.api is deprecated in favor of 
    pythonanywhere.api.base for call_api and get_api_endpoint
    and pythonanywhere.api.webapp for Webapp
    """,
    DeprecationWarning
)
