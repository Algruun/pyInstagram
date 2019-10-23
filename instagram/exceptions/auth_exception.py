from instagram.exceptions.instagram_exception import InstagramException


class AuthException(InstagramException):
    def __init__(self, username: str, message: str = ""):
        super().__init__(f"Cannot auth user with username '{username}': {message}")
