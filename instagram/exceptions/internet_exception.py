from instagram_api.exceptions.instagram_exception import InstagramException
from requests.exceptions import HTTPError


class InternetException(InstagramException):
    def __init__(self, exception: Exception):
        if isinstance(exception, HTTPError):
            super().__init__(
                f"Error by connection with Instagram to '{exception.request.url}' with response code "
                f"'{exception.response.status_code}'"
            )
            self.request = exception.request
            self.response = exception.response
