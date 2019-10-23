from instagram.exceptions.instagram_exception import InstagramException


class UnexpectedResponse(InstagramException):
    def __init__(self, exception: Exception, url):
        super().__init__(
            f"Get unexpected response from '{url}'\nError: {str(exception)}"
        )
