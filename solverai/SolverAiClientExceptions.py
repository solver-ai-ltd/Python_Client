class SetupInExecutionException(Exception):
    def __init__(self, message=None):
        if message is None:
            message = "Setup not complete retry later."
        super().__init__(message)


class SolverAiDrainingException(Exception):
    def __init__(
        self,
        status_code=503,
        detail="Draining",
        retry_after_seconds=None,
        message=None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.retry_after_seconds = retry_after_seconds

        if message is None:
            message = f"{status_code} {detail}"
            if retry_after_seconds is not None:
                message += f" (retry after {retry_after_seconds}s)"

        super().__init__(message)
