class SetupInExecutionException(Exception):
    def __init__(self, message=None):
        if message is None:
            message = "Setup not complete retry later."
        super().__init__(message)
