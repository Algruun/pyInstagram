from instagram.exceptions.auth_exception import AuthException


class CheckpointException(AuthException):
    def __init__(self, username: str, checkpoint_url: str, navigation, types):
        super().__init__(username, "need verification by checkpoint")
        self.checkpoint_url = checkpoint_url
        self.navigation = navigation
        self.types = types
