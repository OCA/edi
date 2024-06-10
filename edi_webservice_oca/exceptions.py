from requests.exceptions import HTTPError


class EDIWebserviceSendHTTPException(HTTPError):
    """Exception raised when an HTTP error occurs during a webservice call."""
